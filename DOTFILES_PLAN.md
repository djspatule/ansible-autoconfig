# Dotfiles Plan

## Short Answer

Yes.

Ansible can:

- install `stow`
- place the dotfiles repository or dotfiles subtree on the machine
- run `stow` for selected packages
- gate packages per host or host group

That is a good direction if you want one repository to remain the source of
truth while still benefiting from Stow's package model.

## Current Status

The first slice is now implemented in the server role.

Current behavior:

- installs `stow` through the server base package list
- clones `https://github.com/djspatule/omarchy-dotfiles.git`
- runs `stow --restow` as the target user
- only stows the `bash` package by default

This is intentionally small so the Stow path can be proven before riskier
packages are added.

## Recommended Model

Use Ansible as the orchestrator and Stow as the placement tool.

That means:

- Ansible decides what host gets what packages
- Stow handles symlink creation into `$HOME`
- host vars control package selection

Do not invert that relationship.

Bad model:

- make Stow the main system configurator and let Ansible just shell out blindly

Better model:

- keep Ansible in charge of package install, repo sync, prerequisites, user
  context, and host selection
- use Stow only for the dotfile placement step

## Proposed Repository Shape

When you are ready to merge the dotfiles repo into this project, the cleanest
first structure is:

```text
dotfiles/
  bash/
    .bashrc
  espanso/
    .config/espanso/match/base.yml
  hypr/
    .config/hypr/...
  ssh/
    .ssh/config
  wireplumber/
    .config/wireplumber/...
```

That mirrors a normal Stow repo.

Then Ansible can manage:

- where the `dotfiles/` tree lives on disk
- which packages are stowed on each host
- which packages are excluded because they are too private or too
  machine-specific

## First Safe Ansible Integration

The first iteration should not try to stow everything.

Start with low-risk packages only:

- `bash`
- maybe `espanso` after review
- maybe app config like `opencode`

Do not start with these:

- `ssh`
- host mount scripts
- `hypr`
- anything with private hostnames, key paths, or monitor-specific assumptions

## Suggested Ansible Variables

When you implement it, a good variable model is:

```yaml
dotfiles_enabled: true
dotfiles_repo_root: /opt/ansible-pull/dotfiles
dotfiles_target_user: lion
dotfiles_stow_dir: /home/lion
dotfiles_packages:
  - bash
  - espanso
```

Then the role logic would roughly be:

1. install `stow`
2. ensure target user/home exists
3. ensure the dotfiles tree exists locally
4. run `stow <package>` as the target user

## Why This Is Better Than A Shell Script Alone

Because Ansible can also encode:

- package prerequisites
- OS-specific behavior
- user creation
- host-specific package selection
- idempotent checks
- future rollback or drift inspection

Stow alone cannot do that cleanly.

## Important Risks

### Secrets

Some current dotfiles are not generic dotfiles.

Examples that should be reviewed before merge:

- `.ssh/config`
- personal Espanso snippets
- server mount scripts
- anything containing email addresses, private hostnames, local IPs, or key
  paths

These should either:

- stay out of the generic package set
- be templated by Ansible
- or move into a host-specific private layer later

### Desktop Specificity

Some current packages are tied to a very specific machine or DE/WM.

Examples:

- Hyprland config
- audio policy scripts
- freebox/systemd user units

These should be host-selected, not globally applied.

## Recommended Next Step

When you decide to start the actual migration, the first implementation step
should be:

1. add `stow` to the workstation package path
2. create a dedicated Ansible-managed `dotfiles/` subtree in this repo
3. migrate one low-risk package such as `bash`
4. validate the Stow workflow on one non-critical machine

That is the smallest serious slice.
