## 1. Timestamp Adaptation

- [x] 1.1 Update the original update schema so `published` validates with Zod's ISO datetime schema and transforms to a `Date`.
- [x] 1.2 Validate non-empty `published` timestamps with Zod's ISO datetime schema before storing update data.
- [x] 1.3 Format parsed `Date` values with browser local timezone semantics using `Intl.DateTimeFormat` during render.
- [x] 1.4 Keep updates without `published` timestamps valid by producing no timestamp value.
- [x] 1.5 Raise a user-facing updates display error when a non-empty `published` timestamp fails ISO datetime validation.

## 2. Fetch and Page Integration

- [x] 2.1 Use the existing Zod schema layer, including `z.iso.datetime()`, to validate update publication timestamps at the fetch/adaptation boundary.
- [x] 2.2 Let `fetchUpdates` return schema-adapted updates with parsed `Date` values before returning updates data to React Query.
- [x] 2.3 Update update card rendering to format the parsed `Date` without parsing source strings during render.
- [x] 2.4 Avoid passing raw publication timestamp strings into update card rendering after successful adaptation.
- [x] 2.5 Show a clear updates-page error when timestamp adaptation fails.
- [x] 2.6 Verify the visible timestamp remains compact inside update card metadata on desktop and mobile layouts.

## 3. Verification

- [x] 3.1 Add focused coverage for valid ISO timestamps, missing timestamps, and invalid ISO timestamp error behavior at the fetch/adaptation boundary if the webapp has an appropriate test layer available during implementation.
- [x] 3.2 Run the narrowest useful webapp verification task.
- [x] 3.3 Run `task check` before finishing when feasible.
