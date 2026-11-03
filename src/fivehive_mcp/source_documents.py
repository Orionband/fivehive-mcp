"""Normalize a document resource supplied by an external document connector.

The MCP intentionally does not authenticate to Google. Codex (or another
authorized client) retrieves the document through its Google Drive connector
and passes the resulting Google Docs resource to ``ingest_source_document``.
"""

import hashlib
import json
import re
from datetime import datetime, timezone

URL_RE = re.compile(r"docs\.google\.com/document/d/([A-Za-z0-9_-]+)")


def document_id_from_url(value: str) -> str:
    match = URL_RE.search(value)
    if not match:
        raise ValueError("Expected a Google Docs URL containing /document/d/{id}")
    return match.group(1)


def _walk_tabs(tabs: list[dict], parent: str | None = None):
    for tab in tabs:
        props = tab.get("tabProperties", {})
        tab_id = props.get("tabId") or tab.get("tabId", "")
        yield tab, parent
        yield from _walk_tabs(tab.get("childTabs", []), tab_id)


def _normalize(document: dict, tabs: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    nodes: list[dict] = []
    assets: list[dict] = []
    diagnostics: list[dict] = []
    for tab in tabs:
        tab_id = tab.get("tabId")
        document_tab = tab.get("documentTab") or {"body": tab.get("body", {})}
        inline_objects = document_tab.get("inlineObjects") or document.get("inlineObjects", {})
        for index, structural in enumerate(document_tab.get("body", {}).get("content", [])):
            node_id = f"{tab_id}:{index}"
            if "paragraph" in structural:
                paragraph = structural["paragraph"]
                runs = []
                for element in paragraph.get("elements", []):
                    if "textRun" in element:
                        run = element["textRun"]
                        runs.append({"content": run.get("content", ""), "startIndex": element.get("startIndex"), "endIndex": element.get("endIndex"), "style": run.get("textStyle", {})})
                    if "inlineObjectElement" in element:
                        asset_id = element["inlineObjectElement"].get("inlineObjectId")
                        embedded = inline_objects.get(asset_id, {}).get("inlineObjectProperties", {}).get("embeddedObject", {})
                        assets.append({"assetId": asset_id, "nodeId": node_id, "startIndex": element.get("startIndex"), "endIndex": element.get("endIndex"), "description": embedded.get("description"), "mimeType": embedded.get("mimeType"), "contentUri": embedded.get("imageProperties", {}).get("contentUri")})
                nodes.append({"nodeId": node_id, "tabId": tab_id, "kind": "paragraph", "startIndex": structural.get("startIndex"), "endIndex": structural.get("endIndex"), "style": paragraph.get("paragraphStyle", {}), "bullet": paragraph.get("bullet"), "runs": runs})
            elif "table" in structural:
                table = structural["table"]
                rows = []
                for row in table.get("tableRows", []):
                    cells = []
                    for cell in row.get("tableCells", []):
                        cells.append({"content": cell.get("content", []), "rowSpan": cell.get("rowSpan", 1), "columnSpan": cell.get("columnSpan", 1)})
                    rows.append(cells)
                nodes.append({"nodeId": node_id, "tabId": tab_id, "kind": "table", "startIndex": structural.get("startIndex"), "endIndex": structural.get("endIndex"), "rows": rows})
            elif "sectionBreak" in structural:
                continue
            else:
                unknown = next(iter(structural), "unknown")
                nodes.append({"nodeId": node_id, "tabId": tab_id, "kind": unknown, "startIndex": structural.get("startIndex"), "endIndex": structural.get("endIndex")})
                diagnostics.append({"code": "UNKNOWN_ELEMENT", "severity": "blocking", "source": {"tabId": tab_id, "nodeId": node_id}, "message": f"Unsupported Google Docs element: {unknown}"})
    return nodes, assets, diagnostics


def snapshot_from_document(document: dict, source_url: str | None = None, tab_ids: list[str] | None = None,
                           suggestions_view_mode: str = "DEFAULT_FOR_CURRENT_ACCESS") -> dict:
    if not isinstance(document, dict):
        raise ValueError("source must be a Google Docs document resource object")
    raw = json.dumps(document, sort_keys=True, separators=(",", ":"))
    snapshot_digest = hashlib.sha256(raw.encode()).hexdigest()
    # Selecting another tab set must not overwrite an earlier saved snapshot.
    selection = json.dumps({"hash": snapshot_digest, "tabs": tab_ids, "suggestions": suggestions_view_mode}, sort_keys=True)
    snapshot_id = hashlib.sha256(selection.encode()).hexdigest()[:24]
    document_id = document.get("documentId")
    if not document_id and source_url:
        document_id = document_id_from_url(source_url)
    if not document_id:
        document_id = f"external-{snapshot_id}"
    raw_tabs = document.get("tabs")
    if not raw_tabs:
        raw_tabs = [{"tabProperties": {"tabId": "tab-0", "title": document.get("title", "")}, "documentTab": {"body": document.get("body", {})}}]
    tabs = []
    for tab, parent in _walk_tabs(raw_tabs):
        props = tab.get("tabProperties", {})
        tab_id = props.get("tabId") or tab.get("tabId", "")
        if tab_ids and tab_id not in tab_ids:
            continue
        document_tab = tab.get("documentTab") or {key: tab[key] for key in ("body", "inlineObjects", "positionedObjects", "lists", "namedStyles", "footnotes", "headers", "footers") if key in tab}
        tabs.append({"tabId": tab_id, "title": props.get("title") or tab.get("title", ""), "parentTabId": parent, "index": props.get("index", tab.get("index", 0)), "documentTab": document_tab})
    normalized, assets, diagnostics = _normalize(document, tabs)
    if tab_ids and set(tab_ids) - {tab["tabId"] for tab in tabs}:
        raise ValueError("One or more selected tabs are unavailable")
    return {"snapshotId": snapshot_id, "snapshotHash": f"sha256:{snapshot_digest}", "documentId": document_id, "sourceUrl": source_url, "title": document.get("title", ""), "revisionId": document.get("revisionId"), "extractedAt": datetime.now(timezone.utc).isoformat(), "suggestionsViewMode": suggestions_view_mode, "tabs": tabs, "normalized": normalized, "assets": assets, "diagnostics": diagnostics, "raw": document}
