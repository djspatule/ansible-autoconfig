# Only interactive shells need the prompt, aliases, and local overrides.
[[ $- != *i* ]] && return

HISTCONTROL=ignoreboth:erasedups
HISTSIZE=5000
HISTFILESIZE=10000
shopt -s histappend checkwinsize

if command -v eza >/dev/null 2>&1; then
  alias ls='eza --group-directories-first --icons=auto'
  alias ll='eza -lah --group-directories-first --icons=auto'
  alias la='eza -a --group-directories-first --icons=auto'
else
  alias ls='ls --color=auto'
  alias ll='ls -alF'
  alias la='ls -A'
fi

alias ..='cd ..'
alias ...='cd ../..'
alias gs='git status'
alias dcu='docker compose up -d'
alias dcd='docker compose down'

if command -v bat >/dev/null 2>&1; then
  alias cat='bat --paging=never --style=header,grid'
fi

export TLDR_OPTIONS="${TLDR_OPTIONS:-both}"

if [[ -f ~/.bashrc.local ]]; then
  . ~/.bashrc.local
fi
