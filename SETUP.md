# EarthScape Climate Agency — Setup & Run Guide

Is file ka maqsad: kisi bhi naye PC (jaise center ka PC) par is project ko
setup aur run karne ke liye. Agar Claude Code ko yeh file di jaye, woh in
steps ko follow karke khud setup + run kar sakta hai.

## Project kya hai

Flask (Python) web app — EarthScape Climate Agency ka Big Data/climate
monitoring platform. Backend: Flask + MongoDB Atlas (cloud database).
Poori detail README-level cheezein neeche hain.

## Zaroori cheezein (prerequisites)

1. **Python 3.11+** installed hona chahiye (`python --version` se check karein)
2. **Internet connection** — MongoDB Atlas (cloud database) aur live weather
   API (Open-Meteo) ke liye zaroori hai. Koi local database install nahi
   karni — database cloud par hai.
3. Is poore project folder (`EarthScape_Climate_Agency_E-Project`) ka copy
   naye PC par hona chahiye, **`.env` file samet** — `.env` usually
   `.gitignore` me hoti hai, isliye agar project Git/GitHub se copy kiya
   hai to `.env` file alag se copy karni hogi (USB, cloud drive, ya
   manually paste karke).

## Setup steps (naya PC par pehli dafa)

Yeh sab commands project folder ke andar, terminal/PowerShell me chalayein:

```powershell
# 1. Virtual environment banayein
python -m venv venv

# 2. Activate karein (Windows PowerShell)
venv\Scripts\Activate.ps1
# (Agar Git Bash use ho raha hai: source venv/Scripts/activate)

# 3. Dependencies install karein
pip install -r requirements.txt
```

### Naya PC par Python 3.11 na ho (jaise Python 3.14 already installed hai)

`requirements.txt` ke pinned versions (numpy 1.26.4, pandas 2.2.2,
scikit-learn 1.5.1) sirf Python ≤3.12 ke liye prebuilt wheels rakhte hain —
Python 3.13/3.14 par pip inhe source se build karne ki koshish karega, jo
bina C++ build tools ke fail ho jata hai. Agar sirf Python 3.14 available
ho:

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install --only-binary=:all: "pandas>=2.2.3" "numpy>=2.0" "scikit-learn>=1.5"
venv\Scripts\python.exe -m pip install Flask==3.0.3 Flask-Login==0.6.3 Flask-PyMongo==2.3.0 pymongo==4.8.0 Werkzeug==3.0.3 python-dotenv==1.0.1 APScheduler==3.10.4 Flask-Mail==0.10.0 itsdangerous==2.2.0 dnspython==2.8.0
```

## `.env` file check karein

Project root me `.env` file honi chahiye is jaisi (agar nahi hai to
`.env.example` ko copy karke `.env` banayein aur values fill karein):

```
SECRET_KEY=<koi bhi random secret string>
MONGO_URI=mongodb+srv://earthscape100_db_user:<PASSWORD>@cluster0.f8zteor.mongodb.net/earthscape?retryWrites=true&w=majority&appName=Cluster0
FLASK_ENV=development
GMAIL_USER=<optional, email bhejne ke liye>
GMAIL_APP_PASSWORD=<optional, Gmail App Password>
```

- **MONGO_URI**: yeh MongoDB Atlas (cloud) ka connection string hai.
  Database cloud par hai, isliye same `.env` (same password) kisi bhi PC
  se use karne par **wahi data** dikhega jo pehle se Atlas me save hai —
  koi local database setup nahi karni.
- **GMAIL_USER / GMAIL_APP_PASSWORD**: agar khaali chhod diye, app tab bhi
  chalegi — password-reset email bhejne ki jagah link server console me
  print ho jayegi (poora flow kaam karta hai, sirf real email nahi jaati).

### `mongodb+srv://` DNS timeout (app start hote hi hang ho jaye)

Agar `python run.py` chalane par app kuch bhi print kiye bina hang ho
jaye (na error, na "Running on http://..."), yeh usually router/network
ka DNS `mongodb+srv://` ke SRV+TXT lookup ko resolve nahi kar pa raha —
`Flask-PyMongo` ka `mongo.init_app()` is lookup par eagerly block ho jata
hai. Fix: Atlas dashboard → cluster → **Connect → Drivers** se **standard
(non-SRV) connection string** le kar `.env` me daal dein — is format me:

```
MONGO_URI=mongodb://<user>:<password>@<shard-00>.mongodb.net:27017,<shard-01>.mongodb.net:27017,<shard-02>.mongodb.net:27017/earthscape?ssl=true&replicaSet=<name>&authSource=admin&retryWrites=true&w=majority
```

Yeh SRV DNS lookup ki zaroorat hi khatam kar deta hai, poori tarah
`mongodb+srv://` jaisa hi kaam karta hai.

## App run karna

```powershell
venv\Scripts\python.exe run.py
```

Phir browser me kholein: **http://127.0.0.1:5000**

Server band karne ke liye terminal me `Ctrl+C` dabayein.

## Claude Code ko bolne ka tareeqa (naye PC par)

Naye PC par Claude Code khol kar itna kehna kaafi hai:

> "Is project ko SETUP.md file ke hisaab se setup aur run kar do."

Claude khud:
1. Python/venv check karega
2. `pip install -r requirements.txt` chalayega
3. `.env` file maujood hai ya nahi verify karega (agar nahi hai to
   ismein di gayi template se banane ko kahega)
4. `run.py` se server start karega
5. MongoDB Atlas connection test karega

## Important notes

- **Data cloud par hai**: kisi bhi PC se chalayein, same MongoDB Atlas
  account ka data (users, ingested records, alerts, tickets) dikhega —
  kyunki `MONGO_URI` cloud database ko point karta hai, local nahi.
- **Local files** (`app/hdfs_sim/raw/`, `app/hdfs_sim/processed/`) us PC
  ke folder me hi rehti hain — yeh HDFS-simulation ke liye ingest kiya
  hua raw data aur processing-job results hain. Yeh PC-specific hain
  (copy nahi hoti jab tak khud copy na karein), lekin app in ke bina bhi
  chal jaati hai — sirf ingestion/processing dobara chalani hogi.
- **MongoDB password kabhi na bhoolein**: agar `.env` file kho jaye,
  MongoDB Atlas se purana password wapis nahi milta — sirf naya set ho
  sakta hai (Atlas dashboard → Database Access → Edit Password). Is
  `.env` file ko kisi mehfooz jagah (USB, private cloud folder) rakhein.
- Agar app pehli baar kisi naye PC par khulti hai to Windows Firewall
  permission maang sakta hai — allow kar dein taake localhost pe server
  chal sake.

## Tech stack summary

- **Backend**: Flask (Python), Flask-Login (auth), Flask-Mail (email)
- **Database**: MongoDB Atlas (cloud)
- **Data processing**: Simulated HDFS (local file partitioning) +
  simulated MapReduce (Python multiprocessing)
- **ML**: scikit-learn (trend prediction + anomaly detection)
- **Frontend**: Server-rendered HTML (Jinja2) + vanilla JS, Chart.js for
  graphs, Vanta.js/Three.js for the live weather visual, Lucide icons

## App structure (blueprints)

Har feature apna Flask blueprint hai, `app/__init__.py` me registered:
`public` (landing page, no login), `auth` (login/register/password reset —
sab ek hi split-panel `auth/combined.html` template se serve hote hain),
`dashboard`, `ingestion`, `processing`, `ml`, `viz`, `alerts`,
`predictions`, `realtime`, `support`, `users` (admin-only), `settings`
(profile/password — sab logged-in users ke liye).

## UI / Branding

- **Design tokens**: `static/css/main.css` ke top par `:root` me sab
  colors hain — background `#161A30`, surface `#31304D`, muted text
  `#B6BBC4`, primary text `#F0ECE5` (dark theme); light theme reversed.
  Koi bhi color change karna ho to sirf yeh tokens edit karein, poore app
  me automatically apply ho jayega.
- **Logo**: `static/images/logo.png` — "E" monogram, transparent PNG. Har
  jagah (favicon, sidebar, auth pages) yehi ek file use hoti hai.
- **Auth illustration**: `static/images/auth_illustration.png` — login/
  register split-panel ki left-side illustration.
- **Live weather widget**: `static/js/sky-hero.js` + `.sky-hero` CSS —
  landing page aur dashboard dono isi shared component ko use karte hain.
  Clear-sky condition me VANTA 3D clouds hat jate hain (sirf CSS
  gradient), baaki conditions (cloudy/rain/storm) me VANTA.CLOUDS chalta
  hai. Performance ke liye VANTA `scale: 0.65` (mobile: `0.55`) par
  render hota hai.

## Testing

`TESTING.md` me poore app ka manual testing checklist hai — har page,
har role (analyst/admin), dono themes ke liye. UI/behavior change karne
ke baad usi file se guzar kar verify karein.

## Hadoop / HDFS — what's real vs. simulated (important, read this)

This project does **not** run a real Hadoop cluster. `app/hdfs_sim/client.py`
and `app/mapreduce/jobs.py` are an honest **local simulation** of the two
HDFS/MapReduce properties that matter for the app's logic:

1. **Partitioning** — ingested CSVs are written to
   `raw/<source_type>/<year>/<month>/<day>/*.csv`, the same layout Hive/HDFS
   partition pruning uses, so a job can target a date range without scanning
   everything.
2. **Write-once blocks** — each ingested file is named `<time>_<uuid>.csv`
   and is never overwritten, mirroring HDFS append-only block files.
3. **Map → Shuffle → Reduce** — `app/mapreduce/jobs.py` genuinely computes
   per-group statistics (mean/min/max/stddev) and z-score anomalies from the
   real ingested data, using Python's `multiprocessing.Pool` to parallelize
   the map phase across CPU cores instead of across cluster nodes.

**Why simulated instead of real:** running an actual Hadoop/HDFS cluster
needs a Linux environment (or WSL2), Java, and several GB of setup that
isn't practical for a single-machine college demo/grading environment. The
simulation preserves the same partitioning and map/shuffle/reduce shape so
the application logic, analytics, and ML pipeline are unaffected by the
swap.

**How to swap in real Hadoop later**, if required for grading/demo:

1. Install Hadoop (single-node "pseudo-distributed" mode is enough) — needs
   Java 8/11, and Linux or WSL2 on Windows. Follow the official Apache
   Hadoop single-node setup guide.
2. Start HDFS (`start-dfs.sh`) and put the `raw/` directory tree onto HDFS
   (`hdfs dfs -put`).
3. Replace the two functions in `app/hdfs_sim/client.py`
   (`write_partitioned`, `list_all_blocks`/`read_blocks_as_dicts`) with
   equivalents using `hdfs3`, `pyarrow.fs.HadoopFileSystem`, or
   `pywebhdfs` — the rest of the app (ingestion, MapReduce jobs, ML,
   dashboards) calls only these functions and does not need to change.
4. Replace `multiprocessing.Pool` in `app/mapreduce/jobs.py` with a real
   Hadoop Streaming job (`hadoop jar hadoop-streaming.jar -mapper ... -reducer ...`)
   invoked via `subprocess`, keeping the same map/reduce function bodies as
   the mapper/reducer scripts.

No part of the app currently claims Hadoop is running when it isn't — the
UI labels this as "MapReduce-style" processing, and `app/hdfs_sim/client.py`'s
own docstring documents the simulation.


cd D:\EarthScape_Climate_Agency_E-Project
venv\Scripts\python.exe run.py
