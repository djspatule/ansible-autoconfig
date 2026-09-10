# Autonomous review build — state

Branch: review/security-functionality-2026-09
Base: 1f1a5ee

## Phase status
- P1 review fan-out: features agent COMPLETE; security + functionality agents
  died on a session limit. Orchestrator did the security verification directly
  against the live host, which is stronger evidence than a code-read anyway.
- P2 verification: in progress.
- P3 implementation: 5 fixes committed on the branch, pending live verification.

## CONFIRMED by orchestrator (live host + code, not agent claims)

S1 CRITICAL  homepage container mounts /var/run/docker.sock RW (root-equivalent
   on the host) AND is published on 0.0.0.0:3000 serving HTTP 200 with no auth,
   AND port 3000 is absent from server_lan_only_published_ports. Caddy correctly
   returns 401 on homepage.dinnizer.com, so the auth is bypassed by going direct.
   Evidence: docker inspect homepage -> RW=True; curl http://192.168.1.100:3000 -> 200;
   curl https://homepage.dinnizer.com -> 401; host_vars/serverannah lan-only list.

S2 MEDIUM  LAN guard is TCP-only. roles/server/templates/autoconfig-docker-lan-guard.sh.j2
   emits only `-p tcp` rules. 8555/udp (Frigate WebRTC) is published on 0.0.0.0
   with no matching guard rule. Confirmed: `ss -ulnp` shows 0.0.0.0:8555 udp;
   `iptables -S DOCKER-USER | grep -c udp` -> 0.

S3 LOW  ufw inactive on serverannah; DOCKER-USER chain is the only filter.
   The guard chain logic itself is correct (established -> RETURN, LAN -> RETURN, DROP).

S4 GOOD (no action)  Secrets hygiene verified clean: vaulted file really is
   ANSIBLE_VAULT-encrypted, .gitignore covers vault passwords, zero private-key
   blobs across all 3129 history objects, no hardcoded credentials in tracked
   files, historic backups/raspi/* pihole configs carry no pwhash.

## FROM FEATURES AGENT — must be verified before acting
F1 no OnFailure= on autoconfig-pull.service.j2 or the borg backup unit
F2 no /etc/docker/daemon.json -> unbounded json-file container logs, 53GB free
F3 backup gaps: /etc/ansible/secrets and /opt/odoo not in backup_paths; no Odoo
   entry in backup_database_dumps at all
F4 no TimeoutStartSec on the pull unit

## Implementation order (once verified)
1. docker daemon.json log caps (disk-fill risk today)
2. S1 homepage: socket-proxy + close :3000
3. S2 guard UDP
4. F1/F4 notification + timeout wiring
5. F3 backup gaps

## Implemented on this branch (each its own commit, pre-commit gate green)
1. Docker log caps via /etc/docker/daemon.json (946 MB of unbounded logs found,
   frigate alone 650 MB) + Restart docker handler.
2. Homepage: raw docker.sock RW bind replaced with a filtered read-only socket
   proxy (POST denied); homepage bound to the LAN IP; port 3000 added to the
   LAN-only guard.
3. LAN guard now filters UDP as well as TCP (8555/udp was wide open).
4. autoconfig-notify + OnFailure= on the pull and Borg units + TimeoutStartSec
   on both. Topic generated host-side into /etc/ansible/secrets.
5. Backup: Odoo DB dump added (511 tables, previously NO dump at all);
   /etc/ansible/secrets and 8 other paths added; dump runner no longer silently
   skips a missing container and no longer truncates the last good dump.

## Next
- Live-verify all five against serverannah from this branch.
- Then decide on merge to main.
