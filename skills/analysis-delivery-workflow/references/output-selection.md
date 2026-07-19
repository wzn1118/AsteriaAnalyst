# Output Selection Heuristics

Choose a main output by matching audience and task:

- HTML report
  - Best default for management-facing analysis with narrative + charts + sectioned findings.
- Markdown report
  - Best for knowledge-base capture, versioning, and follow-on model editing.
- Excel workbook
  - Best when the user or analyst needs to keep slicing tables after delivery.
- PDF summary
  - Best when the result is mostly fixed, print-like, and not meant for further editing.
- PowerPoint deck
  - Best when the user explicitly needs presentation framing, slide-level pacing, and boardroom delivery.
- Image/chart pack
  - Best as a supporting artifact, not usually as the only main deliverable.

Default bundle:

- main: HTML report
- support: Excel workbook
- support: Markdown source

Escalate to PDF or PPT only when the user's audience or usage clearly calls for it.
