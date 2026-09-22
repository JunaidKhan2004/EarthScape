# EarthScape — Manual Testing Checklist

Har page ke saamne `[ ]` hai — test karne ke baad `[x]` kar dein. Test dono
themes (dark + light, top-right sun/moon icon se switch) aur dono roles
(analyst + admin) ke sath karein jahan zikar ho.

Server start: `venv\Scripts\python.exe run.py` → **http://127.0.0.1:5000**

Test accounts (agar maujood hain):
- Admin: `admin.demo@test.com` / `Admin1234`
- Analyst: `analyst.demo@test.com` / `Analyst123`

---

## 1. Public Landing Page (`/`)

- [ ] Page load hoti hai, koi console error nahi
- [ ] Full-screen weather hero dikhta hai, background live weather condition ke mutabiq hai (clear/cloudy/rain/storm)
- [ ] Header transparent hai, "EarthScape" text background ke hisaab se readable hai (dark bg → light text, light bg → dark text)
- [ ] Clock (time + date) live update ho raha hai
- [ ] Temperature, condition, humidity, wind sahi dikh rahe hain
- [ ] City search bar kaam karta hai (e.g. "London" search karke weather change hota hai)
- [ ] "Use my location" button GPS permission maangta hai aur kaam karta hai
- [ ] Galat city search par error message dikhta hai
- [ ] "7-Day Climate Forecasts" section (agar koi approved prediction ho) sahi cards me dikhta hai
- [ ] Mobile width (~375px) par layout tootta nahi

## 2. Auth — Login (`/auth/login`)

- [ ] Split-panel layout: illustration left, form right
- [ ] Header transparent, logo/text readable
- [ ] "Login"/"Register" tab pill sahi se switch hota hai (illustration side bhi flip hoti hai, animated)
- [ ] Empty email/password ke sath submit karne par **error message dikhta hai** (yeh bug tha, ab fix hona chahiye)
- [ ] Galat email format par error dikhta hai
- [ ] Sahi credentials se login → `/dashboard/` par redirect
- [ ] Galat credentials par "Invalid email or password" flash message
- [ ] Password show/hide eye icon kaam karta hai
- [ ] "Forgot password?" link `/auth/forgot-password` par le jata hai
- [ ] Already logged-in user manually `/auth/login` URL type kare to sidebar/header (app chrome) nahi aata — sirf clean login form

## 3. Auth — Register (`/auth/register`)

- [ ] Tab switch se yahan pahunch sakte hain (bina URL change ke bhi)
- [ ] Empty name/email/password ke sath submit → **error messages dikhte hain**
- [ ] Password < 6 characters par error
- [ ] Password strength bar type karte waqt live update hoti hai
- [ ] Naya account register karne par → default role "analyst", turant login ho kar dashboard par redirect
- [ ] Duplicate email se register try karein → "already exists" error

## 4. Auth — Forgot Password (`/auth/forgot-password`)

- [ ] Same split-panel design jaisa login/register
- [ ] Email submit karne par generic success message ("if an account exists...")
- [ ] `.env` me `GMAIL_USER` khaali ho to reset link server console/log me print hoti hai

## 5. Auth — Reset Password (`/auth/reset-password/<token>`)

- [ ] Valid token ke sath page khulta hai
- [ ] Invalid/expired token → "invalid or expired" error, forgot-password par redirect
- [ ] Password aur confirm-password match na karein to error
- [ ] Password < 6 chars par error
- [ ] Successful reset → login page par redirect, naye password se login hota hai

## 6. Dashboard (`/dashboard/`)

### Analyst view
- [ ] "Analyst Workspace" heading, role badge sahi
- [ ] Stat tiles: Records ingested, Processing jobs, My forecasts, Awaiting approval, Approved — sahi numbers
- [ ] **"Records ingested by source" aur "Activity, last 7 days" charts render hote hain** (yeh bug tha, ab fix hona chahiye)
- [ ] 20 second baad stats/activity **automatically refresh hote hain** (Network tab me `/dashboard/api/stats` 200 dena chahiye, `/api/stats` nahi)
- [ ] "My Tools" cards sab clickable hain aur sahi page par le jate hain
- [ ] "My Recent Forecasts" aur "Recent Activity" feed sahi data dikhate hain

### Admin view
- [ ] "Admin Control Center" heading
- [ ] Pending predictions banner dikhta hai (agar koi pending ho)
- [ ] Extra stat tiles: Unacknowledged alerts, Forecasts pending, Live streams, Active thresholds, Registered users, Open tickets
- [ ] Charts yahan bhi render hote hain, stats auto-refresh hote hain
- [ ] "Administration" cards (Users, Alerts, Realtime, Support, etc.) sab kaam karte hain

## 7. Sidebar / Navigation (authenticated pages)

- [ ] Sidebar sab links dikhata hai: Dashboard, Ingestion, Processing, ML, Visualization, Alerts, Predictions, Real-time, Support, Settings
- [ ] Admin ko extra "Users" link dikhta hai, analyst ko nahi
- [ ] Active page ka link highlight hota hai (glow indicator)
- [ ] Mobile width par sidebar hide ho jati hai, hamburger menu se drawer khulta hai
- [ ] Top-right user menu: naam/email/role sahi, "Logout" confirm modal dikhata hai
- [ ] Theme toggle (sun/moon) dark/light switch karta hai aur poore app me consistent rehta hai

## 8. Settings (`/settings/`)

- [ ] Profile card: naam edit karke save karne se naam update hota hai
- [ ] Email field disabled hai (edit nahi ho sakta)
- [ ] Password change: galat current password par error
- [ ] Naya password < 6 chars ya mismatch par error
- [ ] Sahi se password change hone ke baad naye password se dobara login ho sakta hai

## 9. User Management (`/users/`) — Admin only

- [ ] Analyst is page par 403 milta hai
- [ ] Sab registered users list me dikhte hain (naam, email, role)
- [ ] Role dropdown se kisi user ka role change karke save karein — turant reflect hota hai
- [ ] Apna khud ka role change nahi kar sakte ("(you)" dikhta hai)

## 10. Data Ingestion (`/ingestion/`)

- [ ] CSV upload form kaam karta hai
- [ ] "Simulate data" button se test data generate hoti hai
- [ ] Upload ke baad records count dashboard par badh jata hai

## 11. Processing (`/processing/`)

- [ ] "Run" job trigger hota hai
- [ ] Job complete hone ke baad results/status dikhte hain

## 12. ML (`/ml/`)

- [ ] Prediction/anomaly detection form kaam karta hai
- [ ] Results sahi dikhte hain

## 13. Visualization (`/viz/`)

- [ ] Source dropdown change karne par charts update hote hain
- [ ] Bar chart (mean/min/max) aur line chart (trend) dono render hote hain
- [ ] Anomaly list sahi dikhta hai
- [ ] Theme switch karne par chart colors bhi update hote hain

## 14. Alerts (`/alerts/`)

- [ ] Triggered alerts list dikhti hai
- [ ] Analyst: acknowledge kar sakta hai
- [ ] Admin: threshold create/deactivate kar sakta hai, analyst nahi

## 15. Predictions (`/predictions/`)

- [ ] Analyst: forecast generate kar sakta hai (status "pending" set hoti hai)
- [ ] Admin: pending predictions dikhte hain, approve/reject kaam karta hai
- [ ] Approved prediction public landing page par dikhne lagti hai

## 16. Real-time (`/realtime/`)

- [ ] Status dikhta hai (kaunsa stream active hai)
- [ ] Admin: start/stop kaam karta hai
- [ ] Analyst: start/stop button nahi dikhta / disabled hai

## 17. Support (`/support/`)

- [ ] Naya ticket create kar sakte hain
- [ ] Analyst apne tickets dekh sakta hai
- [ ] Admin sab tickets dekh sakta hai aur resolve kar sakta hai

## 18. Cross-cutting checks

- [ ] Poore app me koi bhi jagah text background ke sath invisible/low-contrast nahi hai (dark aur light theme dono me)
- [ ] Sab buttons/links ka naya color palette (#161A30 / #31304D / #B6BBC4 / #F0ECE5) consistent hai, koi purana blue reh nahi gaya
- [ ] Logo (naya "E" monogram) sab jagah sahi dikh raha hai — favicon, sidebar, auth pages
- [ ] 404 page (`/kuch-bhi-random`) sahi dikhta hai
- [ ] Browser console me koi JS error nahi (sab pages par F12 → Console check karein)
