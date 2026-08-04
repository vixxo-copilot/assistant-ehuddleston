# Microsoft Forms Survey Builder

Cursor skill: grill the survey design one question at a time, then create the
Form in Microsoft Forms.

```powershell
py -3 -m pip install msal requests
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py auth
py -3 .agents/skills/ms-forms-survey-builder/scripts/ms_forms_client.py create --spec path\to\spec.json
```

See `SKILL.md` for the full workflow.
