# Microsoft Forms API — question payloads

Undocumented API used by the Forms web UI. Base:

```text
https://forms.office.com/formapi/api/{tenantId}/users/{userId}/forms('{formId}')
```

Auth scope: `https://forms.office.com/.default`

## Create form

`POST .../users/{userId}/forms`

```json
{ "title": "My survey", "description": "Optional subtitle" }
```

Group-owned variant (not used by default):

`POST .../groups/{groupId}/forms` with `{ "title": "..." }`

## Add question

`POST .../forms('{formId}')/questions`

Shared fields: `title`, `type`, `id` (empty ok), `order`, `isQuiz`, `required`,
`questionInfo` (stringified JSON for most types).

### Choice — `Question.Choice`

`ChoiceType`: `1` single, `2` multi-select.

```json
{
  "type": "Question.Choice",
  "title": "Pick one",
  "id": "",
  "order": 1000000,
  "isQuiz": false,
  "required": true,
  "questionInfo": "{\"Choices\":[{\"Description\":\"A\",\"IsGenerated\":true},{\"Description\":\"B\",\"IsGenerated\":true}],\"ChoiceType\":1,\"AllowOtherAnswer\":false,\"OptionDisplayStyle\":\"ListAll\",\"ChoiceRestrictionType\":\"None\",\"ShowRatingLabel\":false}"
}
```

### Text — `Question.TextField`

```json
{
  "type": "Question.TextField",
  "title": "Comments",
  "required": false,
  "questionInfo": "{\"Multiline\":true,\"ShowRatingLabel\":false}"
}
```

### Rating — `Question.Rating`

```json
{
  "type": "Question.Rating",
  "title": "Clarity",
  "required": true,
  "questionInfo": "{\"Length\":5,\"RatingShape\":\"Star\",\"LeftDescription\":\"\",\"RightDescription\":\"\",\"MinRating\":1,\"ShuffleOptions\":false,\"ShowRatingLabel\":false,\"IsMathQuiz\":false}"
}
```

### Date — `Question.DateTime`

```json
{
  "type": "Question.DateTime",
  "title": "Date",
  "required": false,
  "questionInfo": "{\"Date\":true,\"Time\":false,\"ShuffleOptions\":false,\"ShowRatingLabel\":false,\"IsMathQuiz\":false}"
}
```

### NPS — `Question.NPS`

```json
{
  "type": "Question.NPS",
  "title": "How likely are you to recommend us to a friend or colleague?",
  "required": true,
  "questionInfo": "{\"LeftDescription\":\"Not at all likely\",\"RightDescription\":\"Extremely likely\",\"ShuffleOptions\":false,\"ShowRatingLabel\":false,\"IsMathQuiz\":false}"
}
```

### File upload — `Question.FileUpload`

```json
{
  "type": "Question.FileUpload",
  "title": "Upload",
  "required": false,
  "questionInfo": "{\"HasSpecificFileType\":false,\"FileTypes\":{\"Word\":true,\"Excel\":true,\"PowerPoint\":true,\"PDF\":true,\"Image\":true,\"Video\":true,\"Audio\":true},\"MaxFileCount\":1,\"MaxFileSize\":10,\"ShuffleOptions\":false,\"ShowRatingLabel\":false,\"IsMathQuiz\":false}"
}
```

## Not auto-created (manual in designer)

| Type | API notes |
| --- | --- |
| Ranking | Needs follow-up `.../questions('{id}')/choices` posts |
| Likert / Matrix | Uses `Question.MatrixChoice` + `groupId` + choices |

Put these in the spec as `"type": "manual"` with a `note`.

## Designer URL

```text
https://forms.cloud.microsoft/Pages/DesignPageV2.aspx?origin=shell&subpage=design&id={formId}
```

Respond URL (typical):

```text
https://forms.office.com/r/{formId}
```

(Exact respond path may vary; prefer the `responderUri` / similar field from
the create response when present.)
