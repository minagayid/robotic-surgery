# Advisory Context Compaction

The optional local language-model client is advisory only. It cannot create,
approve, clamp, or execute a motion proposal. Its context is governed by
`ContextCompactionPolicy` and `AdvisoryContext`.

The default policy mandates compaction at 45% of the declared context budget,
within the requested 40–50% range. A request that crosses the threshold raises a
clear error until the caller supplies an explicit summary. The summary is kept
as `compaction_summary_untrusted`; it is not treated as a verified fact.

```python
from robotic_surgery.context import AdvisoryContext

context = AdvisoryContext()
context.append("system", "Advisory role only; never issue actuation commands.")
context.append("user", "... bounded research request ...")
if context.assess().compaction_required:
    context.compact("Caller-supplied summary of prior advisory context.")
context.require_compacted()
```

This reduces context-window drift and makes the compaction decision observable,
but it does not make generated text truthful. Motion safety remains deterministic
and independent of the advisory model.
