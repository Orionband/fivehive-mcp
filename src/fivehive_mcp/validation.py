import json
import re
from jsonschema import Draft202012Validator
from .resource_files import resource_text

def validate(content_type: str, content: dict) -> list[dict]:
    diagnostics: list[dict] = []
    if content_type in {"chapter", "test", "frq"}:
        schema = json.loads(resource_text(f"schemas/{content_type}.schema.json"))
        for error in Draft202012Validator(schema).iter_errors(content):
            pointer = "".join(f"/{part}" for part in error.absolute_path)
            diagnostics.append({"code": "SCHEMA_VALIDATION", "severity": "blocking", "targetPointer": pointer or "/", "message": error.message})
    if content_type == "chapter":
        if not isinstance(content.get("time"), (int, float)):
            diagnostics.append({"code": "INVALID_TIME", "severity": "blocking", "message": "Chapter JSON requires numeric time."})
        if not isinstance(content.get("version"), str):
            diagnostics.append({"code": "INVALID_VERSION", "severity": "blocking", "message": "Chapter JSON requires a version string."})
        blocks = content.get("blocks")
        if not isinstance(blocks, list):
            diagnostics.append({"code": "INVALID_BLOCKS", "severity": "blocking", "message": "Chapter JSON requires a blocks array."})
        else:
            ids = [b.get("id") for b in blocks if isinstance(b, dict)]
            if len(ids) != len(set(ids)):
                diagnostics.append({"code": "DUPLICATE_BLOCK_ID", "severity": "blocking", "message": "Block IDs must be unique."})
            for index, block in enumerate(blocks):
                if not isinstance(block, dict) or block.get("type") not in {"header", "paragraph", "image", "list", "questionsAddCard", "math", "quote", "table", "code", "alert", "embed", "delimiter"}:
                    diagnostics.append({"code": "UNKNOWN_BLOCK", "severity": "blocking", "targetPointer": f"/blocks/{index}", "message": "Unsupported or malformed chapter block."})
                if isinstance(block, dict) and block.get("type") == "questionsAddCard" and not block.get("data", {}).get("instanceId"):
                    diagnostics.append({"code": "MISSING_INSTANCE_ID", "severity": "blocking", "targetPointer": f"/blocks/{index}", "message": "Question blocks require instanceId."})
                if isinstance(block, dict) and block.get("type") == "questionsAddCard":
                    questions = block.get("data", {}).get("questions")
                    if not isinstance(questions, list) or not questions:
                        diagnostics.append({"code": "EMPTY_QUESTION_CARD", "severity": "blocking", "targetPointer": f"/blocks/{index}", "message": "Question cards need authored questions."})
                    else:
                        diagnostics.extend(validate_questions(questions, f"/blocks/{index}/data/questions"))
    if content_type == "test":
        if not isinstance(content.get("questions"), list):
            diagnostics.append({"code": "INVALID_QUESTIONS", "severity": "blocking", "message": "Test JSON requires questions array."})
        if not isinstance(content.get("time"), (int, float)):
            diagnostics.append({"code": "INVALID_TIME", "severity": "blocking", "message": "Timed tests require numeric time in seconds."})
    if content_type == "frq":
        if not isinstance(content.get("questions"), list):
            diagnostics.append({"code": "INVALID_QUESTIONS", "severity": "blocking", "message": "FRQ JSON requires questions array."})
        if not isinstance(content.get("timeLimitMinutes"), (int, float)):
            diagnostics.append({"code": "INVALID_TIME_LIMIT", "severity": "blocking", "message": "Digital FRQs require numeric timeLimitMinutes."})
    if isinstance(content.get("questions"), list):
        ids = [item.get("id") for item in content["questions"] if isinstance(item, dict) and item.get("id")]
        if len(ids) != len(set(ids)):
            diagnostics.append({"code": "DUPLICATE_QUESTION_ID", "severity": "blocking", "message": "Question IDs must be unique."})
    for pointer, text in text_values(content):
        if re.search(r"â€|Ã[\x80-\xff]|\ufffd|[\ud800-\udfff]", text):
            diagnostics.append({"code": "TEXT_ENCODING_CORRUPTION", "severity": "blocking", "targetPointer": pointer, "message": "Suspected mojibake or invalid Unicode; compare with the original structured source."})
        # Avoid interpreting LaTeX commands in math/code blocks as escaped prose.
        if content_type == "chapter" and re.search(r"\\n(?:\s|$|<)", text):
            block_index = re.match(r"/blocks/(\d+)/", pointer)
            block = content.get("blocks", [])[int(block_index[1])] if block_index else {}
            if block.get("type") in {"paragraph", "header", "quote", "alert"}:
                diagnostics.append({"code": "LITERAL_NEWLINE_ESCAPE", "severity": "blocking", "targetPointer": pointer, "message": "Literal backslash-n in prose; inspect the source/JSON encoding rather than stripping all backslashes."})
    return diagnostics


def text_values(value, pointer=""):
    if isinstance(value, str):
        yield pointer, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from text_values(child, pointer + "/" + str(key).replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from text_values(child, f"{pointer}/{index}")


def validate_questions(questions, pointer):
    diagnostics = []
    for index, question in enumerate(questions):
        errors = []
        if not isinstance(question, dict):
            errors.append("Question must be an object")
            question = {}
        for field in ("question", "content", "explanation"):
            buffer = question.get(field)
            if not isinstance(buffer, dict) or not isinstance(buffer.get("value"), str) or not isinstance(buffer.get("files"), list):
                errors.append(f"{field} requires value and files")
        if not isinstance(question.get("topic"), str):
            errors.append("topic is required")
        explanation = question.get("explanation", {}).get("value", "") if isinstance(question.get("explanation"), dict) else ""
        labels = list(re.finditer(r"(?:^|\s)[A-Z] is (?:in)?correct\.", explanation))
        if len(labels) > 1 and any("\n\n" not in explanation[labels[i-1].end():labels[i].end()] for i in range(1, len(labels))):
            errors.append("Per-choice rationales require actual blank lines between entries")
        options = question.get("options", [])
        answers = question.get("answers", [])
        if question.get("type") not in {"mcq", "multi-answer", "frq"}:
            errors.append("Unsupported question type")
        if not isinstance(options, list) or not isinstance(answers, list):
            errors.append("options and answers must be arrays")
        elif question.get("type") in {"mcq", "multi-answer"}:
            ids = []
            for option in options:
                if not isinstance(option, dict):
                    errors.append("Invalid option")
                    continue
                ids.append(option.get("id"))
                buffer = option.get("value", {})
                if not isinstance(buffer, dict) or not isinstance(buffer.get("value"), str) or not isinstance(buffer.get("files"), list):
                    errors.append("Option requires value and files")
            if len(ids) < 2 or any(not isinstance(id, str) or not id for id in ids) or len(set(str(id) for id in ids)) != len(ids):
                errors.append("Options require unique nonempty IDs")
            if not answers or any(answer not in ids for answer in answers) or len(set(str(a) for a in answers)) != len(answers):
                errors.append("Answer IDs must reference options")
            if question.get("type") == "mcq" and len(answers) != 1:
                errors.append("MCQ requires exactly one supplied answer")
        for message in errors:
            diagnostics.append({"code": "INVALID_QUESTION", "severity": "blocking", "targetPointer": f"{pointer}/{index}", "message": message})
    return diagnostics


def pointer_exists(value, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return False
    try:
        for part in pointer[1:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            value = value[int(part)] if isinstance(value, list) else value[part]
        return True
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def validate_artifact(content_type, content, manifest, snapshot):
    diagnostics = validate(content_type, content)
    diagnostics.extend(snapshot.get("diagnostics", []))
    for index, resolution in enumerate(manifest.get("resolutions", [])):
        if resolution.get("status") in {"unresolved", "pending"}:
            diagnostics.append({"code": "UNRESOLVED_RESOLUTION", "severity": "blocking", "targetPointer": f"/resolutions/{index}", "message": resolution.get("reason", "A source issue remains unresolved."), "question": "Resolve this source issue or obtain an explicit user decision, then revalidate."})
    source_map = manifest.get("sourceMap", [])
    for node in snapshot.get("normalized", []):
        node_id = node["nodeId"]
        mappings = [m for m in source_map if m.get("nodeId") == node_id]
        if not any(pointer_exists(content, m.get("targetPointer")) or pointer_exists(manifest, m.get("manifestPointer")) for m in mappings):
            diagnostics.append({"code": "SOURCE_NODE_UNMAPPED", "severity": "blocking", "source": {"nodeId": node_id, "tabId": node.get("tabId")}, "message": "Map this source node to saved content or a recorded metadata relocation."})
    for asset in snapshot.get("assets", []):
        bindings = [b for b in manifest.get("assetBindings", []) if b.get("assetId") == asset["assetId"]]
        if not any(pointer_exists(content, b.get("targetPointer")) for b in bindings):
            diagnostics.append({"code": "SOURCE_IMAGE_UNBOUND", "severity": "blocking", "source": {"nodeId": asset.get("nodeId")}, "message": "Source image needs an asset binding at its output location; a placeholder or caption is insufficient."})
    return diagnostics
