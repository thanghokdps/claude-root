---
type: llm
---

The design deletes each batch right after uploading it and says only "Errors are logged". Nothing verifies the upload before the delete, nothing says what happens when the job dies between the two steps, and nothing can read the archive back.

PASS if the final reply asks exactly one question (with 2-4 options and a recommended one) that targets this hole: what happens when the upload or the delete fails halfway, or how an upload is verified before rows are deleted. It reads the design first (it cites the batch or delete step), and it does not answer the question itself.
FAIL if the reply bundles several questions, asks something the file already answers (for example the batch size or bucket name), fills the hole with its own assumption ("we'll add a retry") instead of asking, or only summarizes the design.
