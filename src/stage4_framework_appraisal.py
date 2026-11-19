"""Stage 4 — Framework appraisal.

Evaluate sub-references for their contribution to the primary references using
the four calibrated frameworks: GRADE, Bradford Hill, E-value, and QBA.

CALIBRATION: the evaluation LLM is anchored on gold-standard worked examples of
each framework before its judgments on the live corpus are trusted. See the LLM
calibration subsection in paper/02-methodology.md. Prompts are versioned in
src/prompts/ (E-value prototype in progress).

This module is a stub: the LLM step is currently run by hand in calibration
chats. The part that is implemented, the verification layer that checks the
LLM's E-value output, is in src/stage4/.
"""


def appraise(*args, **kwargs):
    raise NotImplementedError("Stage 4 stub — add implementation.")
