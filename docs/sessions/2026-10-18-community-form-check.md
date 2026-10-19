# 2026-10-18 community report form check

Asked to test the Google Form for "Report without GitHub" (community reports step 3). **No form exists yet:** no `forms.gle` / `docs.google.com/forms` URL, no `entry.<id>` prefill, no `REPORTS_SHEET_ID` / `REPORTS_SHEET_GID` or `make sync-reports` anywhere in the repo, `.env.example`, `Makefile`, `app/` or any branch of `origin`. The popup only links to the GitHub issue form (`app/index.html`, "Suggest a change to this venue"). Nothing was submitted and nothing was changed in the app.

Next: owner follows "Step 3 setup" in `docs/community_reports_plan.md` and sends the form link, one prefilled link, and the sheet id + `approved` tab gid. Then a session builds `make sync-reports` + the popup link and tests the form field-by-field (titles must match the plan exactly) with one marked test submission.
