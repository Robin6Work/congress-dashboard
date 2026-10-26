# Congress dashboard data (GitHub + Power BI)

A scheduled GitHub Action downloads the public congress-legislators JSON files each
month, builds the finished tables and member cards, and saves them as one file:
`data/congress_dashboard.json`. Power BI reads that file from a public URL.

## Part 1: Set up GitHub (about 10 minutes)

1. Create a free GitHub account if needed, then **New repository**. Name it (for example
   `congress-dashboard`), set it to **Public**, and create it.
2. Upload this folder's contents to the repository:
   - `scripts/build_dashboard_json.py`
   - `.github/workflows/monthly-build.yml`
   - `data/.gitkeep`
   - `README.md` (optional)

   Upload tip: if your computer hides folders starting with a dot, create the workflow in
   the browser instead: **Add file > Create new file**, type
   `.github/workflows/monthly-build.yml` as the name (typing the slashes creates the
   folders), and paste in the file's contents.
3. In the repository: **Settings > Actions > General > Workflow permissions**, choose
   **Read and write permissions**, and Save.
4. Go to the **Actions** tab, choose **Build congress dashboard JSON**, and click
   **Run workflow**. It takes under a minute.
5. Open the run's log. If you see a line starting `WARNING: ... membership committee IDs
   have no match`, send it to me; the subcommittee ID matching needs a small fix.
6. When it succeeds, `data/congress_dashboard.json` appears in the repository. Your data
   URL is:

   `https://raw.githubusercontent.com/YOUR-USER/YOUR-REPO/main/data/congress_dashboard.json`

   (replace the two placeholders). Paste it in a browser to confirm it loads.

After that it re-runs by itself on the 2nd of each month, or whenever you click Run
workflow. If a repository sits idle for about 60 days, GitHub may pause scheduled runs;
just click Run workflow once to wake it.

## Part 2: Load it in Power BI

1. Open `powerbi_queries.txt`. Replace `YOUR-USER/YOUR-REPO` in the `DataUrl` line with
   your own values.
2. Power BI Desktop > **Transform data** > click an empty spot in the Queries pane >
   Ctrl+V to paste the whole file. If nothing happens, create each query manually:
   Home > New Source > Blank Query > Advanced Editor, paste one query's text, and name it
   to match.
3. Right-click `stgData` and untick **Enable load**. Click **Close & Apply**.
4. Set the data source credentials: **Anonymous**, privacy level **Public**.
5. Model view relationships:

   | One side                       | Many side                          | Cross-filter |
   |--------------------------------|------------------------------------|--------------|
   | Legislators[Bioguide ID]       | Terms[Bioguide ID]                 | Single       |
   | Legislators[Bioguide ID]       | LeadershipRoles[Bioguide ID]       | Single       |
   | Committees[Committee ID]       | MemberCommittees[Committee ID]     | Single       |
   | Legislators[Bioguide ID]       | MemberCommittees[Bioguide ID]      | Both         |
   | Legislators[Bioguide ID]       | MemberCards[Bioguide ID] (1:1)     | Both         |

6. Create the `Page` table and the measures from `powerbi_measures_and_tables.txt`
   (one at a time, as labeled in that file). Add the HTML Content visual with
   `Cards HTML`, plus the slicers described earlier.
7. Publish to the Power BI Service and set the scheduled refresh. Because the file is on
   a public URL, no gateway is needed.

## Changing things later

- Photos: edit `PHOTO_URL_TEMPLATE` in the workflow file.
- Collapsed vs. expanded sections: set `SECTIONS_OPEN` to `"false"` or `"true"` in the
  workflow file.
- Card design or fields: edit `build_card` in the script (ask me and I will).
- More state outlines: add entries to `STATE_SHAPES` in the script.
