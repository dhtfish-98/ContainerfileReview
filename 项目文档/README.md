> 目录已整理：文档在「项目文档」，暂存与缓存放在「Build」。本仓发布源码版；`python3 构建.py --build` 会返回 `OPEN_MANUAL_ADAPTER`，不生成安装包。运行源码命令前先执行 `python3 构建.py --stage --ci`，再进入 `Build/源码`。暂存会恢复原输入路径。现有版本和历史验证记录按各自提交理解。

# ContainerfileReview

**Source version:** [v0.1.0](https://github.com/dhtfish-98/ContainerfileReview/releases/tag/v0.1.0) ([release scope](RELEASES.md)); GitHub source archives only.

Review selected image and user declarations in a local Dockerfile. It runs locally, does not contact targets, and reports review prompts instead of exploit instructions.

## Input and checks

- Input: Dockerfile from a system you own or are authorized to inspect.
- Checks: Mutable FROM references, remote ADD and missing non-root final USER.
- Output: rule, local location and short note. No source snippets, credential values or log identities are printed.

## Run

```sh
python cli.py ./owned-input
python cli.py ./owned-input --json
python -m unittest discover -s tests -v
```

Exit code 0 means no findings, 1 means review findings, 2 means invalid input or read failure. A clean result is not a security guarantee. The input file is read through a bounded regular-file descriptor with a 4 MiB limit.

## Boundaries

This is a line-oriented Dockerfile review; ARG expansion, build graph behavior, image contents and runtime privileges are not resolved. Work only on local, authorized inputs. The analysis does not send data to a service or modify the inspected files.

## Source and policy context

- Technical reference: https://docs.docker.com/build/building/best-practices/
- See [ORIGIN.md](<ORIGIN.md>) for implementation provenance and [VALIDATION.md](<VALIDATION.md>) for checks performed.
- CVP eligibility depends on a real, legitimate defensive task affected by Claude's cyber safeguards and the applicant's organization/identity review; this repository alone does not establish eligibility or approval. [Anthropic CVP guidance](https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude-opus-and-sonnet).

## Reviewed input behavior

Stage aliases inherit known USER declarations. UID 0 remains root regardless of its group. Valid SHA-256 image digests are distinguished from malformed pins. Escape directives and common heredoc bodies are parsed without executing them; build variables and ONBUILD behavior remain review prompts.
