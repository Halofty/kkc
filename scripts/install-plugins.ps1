# 프로젝트 폴더에서 실행: PowerShell> .\scripts\install-plugins.ps1
# (.claude/settings.json 에 이미 등록돼 있어 Claude Code를 이 폴더에서 열면 자동 설치 안내가 뜹니다.
#  수동으로 하고 싶을 때만 이 스크립트를 쓰세요.)
Set-Location (Split-Path $PSScriptRoot -Parent)

# Superpowers (공식 마켓플레이스라 add 단계 없음)
claude plugin install superpowers@anthropic-plugin-directory --scope project

# 카파시
claude plugin marketplace add forrestchang/andrej-karpathy-skills
claude plugin install andrej-karpathy-skills@karpathy-skills --scope project

# I have ADHD
claude plugin marketplace add ayghri/i-have-adhd
claude plugin install i-have-adhd@i-have-adhd --scope project

# Ponytail
claude plugin marketplace add DietrichGebert/ponytail
claude plugin install ponytail@ponytail --scope project

# graphify (스킬은 .claude/skills 에 커밋돼 있음, CLI만 설치)
pip install graphifyy
