# Job Referral Finder — MVP

## Problem
Job seekers miss referral opportunities because they don't know when their connections' companies are hiring for their role. By the time they find out, the window to ask for a referral has often passed.

## Product Vision
"Set it and forget it referral radar." Enter your network once, it runs in the background, relevant roles surface in your inbox. Use it alongside LinkedIn — LinkedIn shows you what's open everywhere, this shows you what's open where you know someone.

## North Star Outcome
A job seeker lands more interviews because they asked for referrals at the right time, instead of cold applying.

## Validation Goal
**10 users, each clicking at least one job in their first email.**

Starting with 3 known job seekers. Success = they open the email, find a relevant role, and click through.

---

## MVP Scope

### In scope
| Feature | Status |
|---|---|
| Subscribe (email, target role, companies to watch) | Done |
| Daily email with AI-matched job listings | Done |
| Unsubscribe | To build |

### Out of scope
- Resume upload
- Multiple target roles per user
- Click tracking
- Company coverage beyond Greenhouse / Ashby / Lever
- Mobile app
- User accounts / dashboard

---

## User Flow

1. User visits the web app and enters their email, target role, and companies to watch
2. Every morning at 8am UTC, the scraper runs and finds open roles at their watched companies
3. Claude filters for roles that match their target role
4. User receives an email with matched roles and a direct link to each job posting
5. User clicks a role → visits the job posting → reaches out to their contact for a referral
6. User can unsubscribe at any time via a link in every email

---

## What "Working" Looks Like
- User opens the email
- At least one job is relevant enough to click
- User knows exactly who to reach out to and why

## What We Are Not Measuring Yet
- Whether the user actually reached out for a referral
- Whether they got referred
- Whether they got an interview

---

## Supported ATS Platforms
- **Greenhouse** — Stripe, Airbnb, Figma, Brex, Discord, Coinbase, Robinhood
- **Ashby** — Notion, Linear, Ramp, Plaid, Mercury, Retool, Airtable, Vercel
- **Auto-probe** — Any company whose name matches their slug on the above platforms

---

## Next After MVP
See backlog in MEMORY.md. Do not build anything else until 3 beta users have clicked at least one job.
