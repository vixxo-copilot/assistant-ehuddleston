# Microsoft Forms Survey Builder

Cursor skill: grill the survey design one question at a time, then create the
Form in Microsoft Forms.

```powershell
py -3 -m pip install -r .agents/skills/ms-forms-survey-builder/requirements.txt
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py validate --spec .agents/skills/ms-forms-survey-builder/examples/nps-pulse.json
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py create --spec .agents/skills/ms-forms-survey-builder/examples/nps-pulse.json --dry-run
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py auth
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py create --spec path\to\spec.json
```

Starter specs: `examples/nps-pulse.json`, `examples/event-rsvp.json`,
`examples/training-feedback.json`.

See `SKILL.md` for the full workflow.
