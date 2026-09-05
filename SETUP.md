# Palisade Setup

## Prerequisites

- A ProxMox VE (PVE) server with root or sufficient API-token access
- Python 3.11+
- Docker (for PostgreSQL)
- Git

---

## 1. Clone the Repo

```bash
git clone https://github.com/alex-cantor/palisade.git
cd palisade
```

## 2. PostgreSQL

Start the database container:

```bash
docker run -d \
  --name palisade-db \
  -p 5432:5432 \
  -v palisade_pgdata:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=postgres \
  postgres:17
```

Create the database and user:

```bash
docker exec -it palisade-db psql -U postgres
```

```sql
CREATE DATABASE ccdc;
CREATE USER ccdc_admin WITH PASSWORD 'your_password_here'; # postgres

ALTER ROLE ccdc_admin SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE ccdc TO ccdc_admin;

\c ccdc
ALTER SCHEMA public OWNER TO ccdc_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO ccdc_admin;

\q
```

## 3. Environment Config

Copy the example env file and fill it in:
```bash
cp engine/.env.example engine/.env
```

Edit `engine/.env`:
| Variable | Description |
|---|---|
| `DB_PASSWORD` | The password you set for `ccdc_admin` above |
| `PROXMOX_HOST` | IP or hostname of your PVE server |
| `PROXMOX_USER` | PVE user (e.g. `root@pam`) |
| `PROXMOX_TOKEN_NAME` | Name of the API token (see below) |
| `PROXMOX_TOKEN_VALUE` | Token UUID from PVE |
| `PROXMOX_NODE` | PVE node name (default: `pve`) |
| `PROXMOX_BRIDGE` | The Linux bridge to attach team VMs to (e.g. `vmbr1`) |

**Creating a ProxMox API token:**
PVE web UI --> Datacenter --> Permissions --> API Tokens --> Add. Give it `PVEAdmin` role (or a scoped role with VM.Clone, VM.Config.*, VM.PowerMgmt).


## 4. Django Setup

```bash
cd engine
python -m venv venv

# Linux/macOS
source venv/bin/activate
# Windows
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

python manage.py migrate
python manage.py create_organizer   # follow the prompts
python manage.py runserver
```

Open http://localhost:8000 and log in with the organizer credentials you just created.

## 5. ProxMox Templates

Before you can provision competition VMs, you need VM templates on your PVE server. Run `engine/create_templates.sh` **on the PVE host** (not your local machine):

```bash
# Copy the script to your PVE server
scp engine/create_templates.sh root@<pve-host>:/root/

# SSH in and run it
ssh root@<pve-host>
bash /root/create_templates.sh
```

This downloads cloud images for ~18 Linux distros and creates PVE templates at VMIDs 9000–9027. It takes a while (lots of large downloads). Once done, you'll see templates in the PVE UI.

> **Storage names:** The script uses `local-lvm` for VM disks and `local` for cloud-init. If your storage pools have different names, edit those values at the top of the script.

> **Bridge name:** The script uses `vmbr0` for templates (they don't need network access to be templatized). Competition VMs use the bridge from your `.env`.

### Linking Templates to Django

After templates exist in PVE, go to the Django admin (`/admin/`) --> Machine Templates. For each template, set the **ProxMox VMID** field to match the VMID in PVE:

| Template name | VMID |
|---|---|
| Debian 12 | 9004 |
| Ubuntu 22.04 | 9013 |
| Rocky Linux 9 | 9022 |
| ... | ... |

(Full VMID list is at the top of `engine/create_templates.sh`.)

---

## 6. Running a Competition

1. Log in as organizer --> **New Competition**
2. Set difficulty, industry, machines (precise mode) or machine count (random mode)
3. **Provision Teams** — creates login accounts for competitors
4. **Provision Infrastructure** — clones ProxMox templates, one set of VMs per team
5. **Go Live** — opens the portal for competitors

---

## Troubleshooting

**`psycopg2` install fails on Linux:** `sudo apt install libpq-dev python3-dev` first.

**ProxMox connection refused:** Check that the API token has the right permissions and that `PROXMOX_VERIFY_SSL=false` if using a self-signed cert.

**Template clone hangs:** Large full clones can take several minutes per VM. The provisioner waits up to 5 minutes per clone — increase `timeout` in `provisioning.py` if needed.

**Wrong bridge:** Team VMs won't get IPs if `PROXMOX_BRIDGE` doesn't match a real Linux bridge on your PVE host. Check `ip link show` on the PVE host.
