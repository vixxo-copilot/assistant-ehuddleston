# Survey spec (JSON)

Write approved specs to `_tmp/ms-forms-survey-builder/<slug>-spec.json`.

## Schema

```json
{
  "title": "Q2 Field Tech Experience Pulse",
  "description": "2-minute pulse on dispatch clarity and tooling. Internal only.",
  "settings": {
    "collect_email": true,
    "one_response_per_person": true
  },
  "questions": [
    {
      "type": "nps",
      "title": "How likely are you to recommend Vixxo as a place to work field tech jobs?",
      "required": true
    },
    {
      "type": "choice",
      "title": "What is the biggest friction in your last 5 jobs?",
      "required": true,
      "multi": false,
      "allow_other": true,
      "choices": [
        "Unclear scope",
        "Parts availability",
        "Customer access",
        "App / paperwork",
        "Travel / routing"
      ]
    },
    {
      "type": "rating",
      "title": "How clear was the work order on your last job?",
      "required": true,
      "length": 5,
      "shape": "Star"
    },
    {
      "type": "text",
      "title": "Anything else we should fix first?",
      "required": false,
      "multiline": true
    },
    {
      "type": "date",
      "title": "Date of the job you are thinking about",
      "required": false
    },
    {
      "type": "file",
      "title": "Optional screenshot of the issue",
      "required": false
    },
    {
      "type": "manual",
      "title": "Rate each dimension (Likert — add in designer)",
      "note": "Likert/Matrix is not auto-created; add after open in designer."
    }
  ]
}
```

## Field rules

| Field | Required | Notes |
| --- | --- | --- |
| `title` | yes | Form title |
| `description` | no | Shown under title |
| `settings.collect_email` | no | Hint only in v1 (designer may still need a toggle) |
| `settings.one_response_per_person` | no | Hint only in v1 |
| `questions[].type` | yes | `choice` `text` `rating` `date` `nps` `file` `manual` |
| `questions[].title` | yes | Question prompt |
| `questions[].required` | no | Default `false` |
| `questions[].choices` | for `choice` | Non-empty string list |
| `questions[].multi` | for `choice` | `true` = multi-select |
| `questions[].allow_other` | for `choice` | Adds Other |
| `questions[].multiline` | for `text` | Long answer |
| `questions[].length` | for `rating` | 1–10, default 5 |
| `questions[].shape` | for `rating` | `Star` (default) or `Number` |
| `questions[].note` | for `manual` | Shown in create summary; skipped by API |

## Create behavior

1. Create empty form with `title` (+ `description` when accepted).
2. POST each non-`manual` question in order.
3. Print designer + respond URLs.
4. List any `manual` questions for the user to add in DesignPageV2.
