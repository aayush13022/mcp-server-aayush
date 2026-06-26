from googleapiclient.discovery import build

from auth import get_credentials


def _get_docs_service():
    return build("docs", "v1", credentials=get_credentials())


def append_to_doc(doc_id: str, content: str) -> dict:
    """Append text to the end of a Google Doc."""
    service = _get_docs_service()

    doc = service.documents().get(documentId=doc_id).execute()
    end_index = doc["body"]["content"][-1]["endIndex"] - 1

    requests = [
        {
            "insertText": {
                "location": {"index": end_index},
                "text": content,
            }
        }
    ]

    return (
        service.documents()
        .batchUpdate(documentId=doc_id, body={"requests": requests})
        .execute()
    )
