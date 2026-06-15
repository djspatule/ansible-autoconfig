# DECISIONS

- **ASSUMED** repo pass is conservative/behaviour-preserving, on a `repo-cleanup`
  branch merged after review (prod pulls `main`). [confirmed by user: "conservator"]
- **DECIDED** kids task = capture current state, not invent. [user #5]
- **DECIDED** manage `oscar`/`romy` accounts but not passwords; no secrets in the
  public repo. Passwords given in chat are NOT stored anywhere. [security]
- **DECIDED** DNS filtering stays network-level (Pi-hole); no per-host DNS. [user #8]
- **DECIDED** keep the legacy bash/starship dotfiles tasks (git-history value);
  do not do the risky collapse under a "conservative" pass. [PLAN A.4]
- **ASSUMED** kids host joins the same ansible-pull daily-timer model as the
  other hosts. Revisit if the old MacBook should instead be pushed to from the
  laptop.
- **OPEN** exact hostname for the kids host (set after recon).
