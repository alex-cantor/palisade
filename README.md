# palisade

A mock CCDC environment generator, to quickly spin up networks on PVE for realistic adversarial simulation.

> Updates regarding the project will be posted at [acantor.me/blog](https://acantor.me/blog)

## About

Ask any CCDC competitor the best way to get good, and their answer will be the same: get experience. It is really hard to do this through only competitions, as there are only a couple of competitions per year. The best way to do this is through mock competitions, so I knew I wanted to build infrastructure to set up mock competitions fast.

I also knew I wanted to have the environment replicate CCDC environments as best as possible. Originally, I was going to provision credentials for my teammates, but one of my teammates (@lolmenow) told me about a portal he was writing to replicate the eCitadel environment--which is very similar to the CCDC environment. I thought this was an awesome idea, so I plan to replicate it. For the project, I think it would be best for there to be three general components: the mock environment generator itself, the CCDC-like interface, and the autonomous red teamer. I'll discuss each in more depth later

Due to the nature of this project (and CCDC itself), I am also excited for potential applications outside of CCDC. In volunteering with the Iowa Air National Guard, I was tasked with helping to configure, deploy, and pentest a vulnerable network for the military personnel to then watch logs. By being able to spin up a network as I will eventually be able to do with palisade, this task will become trivial. In addition to the defensive side, networks could be spun up for practice with red teaming and pentesting.

> Disclosure: I already have access to a ProxMox (PVE) server with root permissions and a ton of resources (70TB of usable storage plus 1/2 PB sitting, waiting to be plugged in) so I am starting off at a better point than most teams. That said, you should be able to replicate this project via a service like Hetzner or OVHCloud for less than $100/month.

## Overview

There are three components, with each stage broken down further.

### 1. Engine (mock environment generator)

The technical components of the engine are the template generator, the randomizer, and the provisioner.

### 2. Interface (CCDC-like web portal)

I think this is going to be the most annoying part. There are two views which I'd like to discuss.

> Note 1: Thanks to `@lolmenow` for the idea--he built his own version of this at https://portal.sakouk.me.
> Note 2: I will be using 

#### Competitor

The Competitor will have the ability to:
- View the Scoreboard (which breaks down everyone's score across categories)
- View and submit Injects (their team's injects, including past and present injects themselves and their associated scores)
- View, access, and snapshot VMs
- Connect remotely to the VMs, via a VPN (I will potentially write an API to Ubiquiti's Unifi, which is what I am using for it)

#### Organizer

The Organizer will have the ability to:
- Generate mock environments (and specify parameters as necessary)
- Provision and distrubute competitor credentials

#### Infra Admin

The Infra Admin owns the infrastructure, and provisions and distributes Organizer credentials.

### 3. Auto-Pwn (Autonomous Red Teamer)

I do not have further details here at the moment.

## Setup

> Note: these instructions were written for Windows but it can be ran on LInux (in fact, Linux will be the primary OS it is meant for--I will write separate Linux instructions shortly)

### 1. Download it
```bash
git clone https://github.com/alex-cantor/palisade.git && cd palisade
```

### 2. Create the PostgreSQL DB

1. Spin up the PostgreSQL container (in PowerShell)
```powershell
docker run -d --name palisade-db -p 5432:5432 -v palisade_pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD=postgres postgres:17
```

2. Create the DB
```powershell
docker exec -it palisade-db psql -U postgres
```

3. Configure user perms
```powershell
CREATE DATABASE ccdc;
CREATE USER ccdc_admin WITH PASSWORD 'your_pass';

ALTER ROLE ccdc_admin SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE ccdc TO ccdc_admin;

\c ccdc
ALTER SCHEMA public OWNER TO ccdc_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO ccdc_admin;
GRANT CREATE, USAGE ON SCHEMA public TO ccdc_admin;

\q
```

### 3. Django Environment Config

0. Navigate to the engine
```powershell
cd engine
```

1. Set up the Virtual Environment
```powershell
python -m venv venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements
```

2. In your `.env` and throughout the app, ensure the proper settings are configured (TODO: make sure everything pulls from the `.env`)


3. Apply migrations, add your first organizer, and run the server
```powershell
python manage.py migrate
python manage.py create_organizer
python manage.py runserver
```
