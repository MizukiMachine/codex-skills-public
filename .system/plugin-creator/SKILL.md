---
name: plugin-creator
description: "Codexプラグインのディレクトリとマニフェストを作成・更新する。plugin.json、個人マーケットプレイス、表示順、再インストール用の更新作業で使う。"
---

# Plugin Creator

## Quick Start

1. scaffold スクリプトを実行する。

```bash
# Plugin 名は lower-case hyphen-case に正規化され、64文字以下でなければならない。
# 生成されるフォルダ名と plugin.json の name は常に同じになる。
# この `SKILL.md` があるスキルルートから実行する。
# 既定では `~/plugins/<plugin-name>` に作成する。
python3 scripts/create_basic_plugin.py <plugin-name>
```

2. リクエストに具体的なメタデータが含まれる場合は `<plugin-path>/.codex-plugin/plugin.json` を編集する。
   scaffold は有効な既定値から始まり、`[TODO: ...]` の placeholder を残してはならない。

3. Codex UI の表示順に plugin を出したい場合は、個人 marketplace entry を生成または更新する。

```bash
# 個人 marketplace entry の既定先は `~/.agents/plugins/marketplace.json`。
python3 scripts/create_basic_plugin.py my-plugin --with-marketplace
```

`--marketplace-name <name>` は、既定の `personal` marketplace 名が既に使われていて、別名の新規 marketplace file を seed する必要がある場合だけ指定する。

```bash
python3 scripts/create_basic_plugin.py my-plugin \
  --with-marketplace \
  --marketplace-name team-local
```

repo/team marketplace は、ユーザーがその保存先を明示した場合だけ使う。

```bash
python3 scripts/create_basic_plugin.py my-plugin \
  --path <repo-root>/plugins \
  --marketplace-path <repo-root>/.agents/plugins/marketplace.json \
  --with-marketplace
```

ユーザーが marketplace path を指定した場合は、そこから reinstall するよう案内する前に、その marketplace が実際にインストール済みか確認する。既定の個人 marketplace file `~/.agents/plugins/marketplace.json` は暗黙に発見されるが、それ以外の marketplace path は自動発見されない。Windows では user profile 配下の対応パスを使う。

4. 必要に応じて任意の companion folder を生成または調整する。

```bash
python3 scripts/create_basic_plugin.py my-plugin \
  --path <parent-plugin-directory> \
  --marketplace-path <marketplace-json-path> \
  --with-skills --with-hooks --with-scripts --with-assets --with-mcp --with-apps --with-marketplace
```

`<parent-plugin-directory>` は plugin folder `<plugin-name>` が作成される親ディレクトリである。例: `~/plugins`。

5. 生成した plugin を渡す前に検証する。

```bash
python3 scripts/validate_plugin.py <plugin-path>
```

開発中の既存 local plugin を更新する場合は scaffold flow を保ち、marketplace file を手編集せず reference に沿う。

```bash
python3 scripts/update_plugin_cachebuster.py <plugin-path>
```

ユーザーが特定の override を明示しない限り、helper の既定 cachebuster を使う。既存 local plugin の反復時に期待される cachebuster と reinstall flow は `references/installing-and-updating.md` を参照する。

## What This Skill Creates

- 既定の marketplace-backed scaffold は個人 marketplace file `~/.agents/plugins/marketplace.json` を使い、plugin は通常 `~/plugins/<plugin-name>/` に置く。
- plugin root を `/<parent-plugin-directory>/<plugin-name>/` に作成する。
- `/<parent-plugin-directory>/<plugin-name>/.codex-plugin/plugin.json` を必ず作成する。
- ingestion path が受け付ける検証済み schema shape で manifest を埋める。
- `--with-marketplace` が指定された場合は `~/.agents/plugins/marketplace.json` を作成または更新する。まだ存在しない場合は、最初の plugin entry を追加する前に personal marketplace root を seed する。
- `<plugin-name>` は skill-creator の命名規則で正規化する。
  - `My Plugin` -> `my-plugin`
  - `My--Plugin` -> `my-plugin`
  - underscore、space、punctuation は `-` に変換する。
  - 結果は lower-case hyphen-delimited で、連続 hyphen は畳む。
- 任意で次を作成できる。
  - `skills/`
  - `hooks/`
  - `scripts/`
  - `assets/`
  - `.mcp.json`
  - `.app.json`

## Marketplace Workflow

- 個人 marketplace の既定作成先は `~/.agents/plugins/marketplace.json`。ここでの "personal marketplace" はこの path にある marketplace を指す。
- repo/team marketplace の作成は `--path` と `--marketplace-path` の両方を指定する明示 opt-in とし、ユーザーが具体的に求めた場合だけ行う。
- `--marketplace-name` は例外経路である。既定の `personal` marketplace 名が既に使われていて、別名の新規 marketplace file を seed する必要がある場合だけ使う。
- 既存 marketplace file の名前変更目的で `--marketplace-name` を使わない。file が既に存在する場合、その top-level `name` は既に一致していなければならない。
- ユーザーが別の marketplace path を指定した場合、その marketplace は `codex plugin marketplace add` による明示インストールが必要だと扱う。
- 任意の `marketplace.json` file から marketplace 名が必要な場合は `scripts/read_marketplace_name.py` を優先する。引数なしでは既定の personal marketplace を読む。明示 path を渡すと repo/team marketplace にも使える。
- どちらの場所でも、生成される source path は `./plugins/<plugin-name>` のままにする。
- marketplace root metadata は top-level `name` と任意の `interface.displayName` をサポートする。
- `plugins[]` の順序を Codex 上の表示順として扱う。ユーザーが明示的に並べ替えを求めない限り、新規 entry は末尾に追加する。
- `displayName` は marketplace の `interface` object に置く。個々の `plugins[]` entry には置かない。
- 生成する marketplace entry には必ず次を含める。
  - `policy.installation`
  - `policy.authentication`
  - `category`
- 新規 entry の既定値は次の通り。
  - `policy.installation: "AVAILABLE"`
  - `policy.authentication: "ON_INSTALL"`
- ユーザーが別の allowed value を明示した場合だけ既定値を上書きする。
- `policy.installation` の allowed value:
  - `NOT_AVAILABLE`
  - `AVAILABLE`
  - `INSTALLED_BY_DEFAULT`
- `policy.authentication` の allowed value:
  - `ON_INSTALL`
  - `ON_USE`
- `policy.products` は override として扱う。ユーザーが product gating を明示的に求めない限り省略する。
- 生成する plugin entry shape:

```json
{
  "name": "plugin-name",
  "source": {
    "source": "local",
    "path": "./plugins/plugin-name"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Productivity"
}
```

- 同じ plugin name の既存 marketplace entry を意図的に置き換える場合だけ `--force` を使う。
- target marketplace file がまだ存在しない場合は、top-level `"name"`、`"displayName"` を含む `"interface"` object、`plugins` array を持つ file を作成し、そこへ新規 entry を追加する。
- brand-new marketplace file の root object は次の形にする。

```json
{
  "name": "personal",
  "interface": {
    "displayName": "Personal"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": {
        "source": "local",
        "path": "./plugins/plugin-name"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

## Required Behavior

- outer folder 名と `plugin.json` の `"name"` は、常に同じ正規化済み plugin name にする。
- 必須構造を削除せず、`.codex-plugin/plugin.json` を残す。
- plugin manifest に `[TODO: ...]` placeholder を残さない。
- companion file を実際に作成していない限り、`apps` と `mcpServers` を `plugin.json` に入れない。
- `hooks` など、validation が reject する未対応 plugin manifest field は省略する。
- 既存 plugin path 内に file を作る場合、意図的に上書きするときだけ `--force` を使う。
- 既存 marketplace の `interface.displayName` は保持する。
- marketplace entry を生成する場合、値が既定値でも `policy.installation`、`policy.authentication`、`category` を必ず書く。
- `policy.products` はユーザーが明示的に override を求めた場合だけ追加する。
- marketplace の `source.path` は、選択した marketplace root からの相対 path として `./plugins/<plugin-name>` にする。
- `--marketplace-name` は、作成する新規 marketplace file の名前を `personal` 以外にする必要がある場合だけ使う。理由はその名前が既に別の場所で使われている、またはインストール済みであること。
- Codex が marketplace file へ書き込むのに approval を必要とする場合は、処理前に approval を求める。ユーザーが自分で書き込みたい場合は正確な scaffold command を提示し、その後の validation や plugin edit から継続する。
- 開発中の既存 local plugin を更新する場合、marketplace config や `marketplace.json` を手編集しない。`references/installing-and-updating.md` と `scripts/update_plugin_cachebuster.py` にある update flow を使う。
- 既定の personal-marketplace flow で `codex plugin marketplace add` を実行するようユーザーに言わない。この command は standard `~/.agents/plugins/marketplace.json` path ではなく、明示的な non-default marketplace 設定用である。
- ユーザーが non-default `--marketplace-path` を指定した場合、reinstall 手順を案内する前に、その marketplace がインストール済みであることを確認する。明示 marketplace が未設定なら `codex plugin marketplace add <path-to-marketplace-root>` を使う。
- marketplace-backed plugin を作成または更新した場合、最終回答の末尾に短い Codex app handoff を入れる。`To view this in the Codex app:` と書き、`View <normalized plugin name>` と `Share <normalized plugin name>` を raw URL や code span ではなく Markdown links にする。
- View deeplink は `codex://plugins/<normalized plugin name>?marketplacePath=<absolute marketplace.json path>` を使う。
- Share deeplink は同じ URL に `&mode=share` を付ける。
- placeholder は実際の正規化済み plugin name と、scaffold された plugin の absolute `marketplace.json` path に置き換える。必要に応じて path segment と query value を URL encode する。
- deeplink に `pluginName` や `hostId` query parameter を追加しない。Codex はユーザーがリンクをクリックした後に両方を導出する。
- marketplace entry が作成または更新されていない場合は、`View <normalized plugin name>` や `Share <normalized plugin name>` の link を出さない。

## Reference to Exact Spec Sample

plugin manifest と marketplace entry の canonical sample JSON が必要な場合は次を使う。

- `references/plugin-json-spec.md`
- `references/installing-and-updating.md`: 既存 local plugin を反復更新するときの update/reinstall guidance と、reinstall 後に新しい thread で反映される挙動。

## Validation

`SKILL.md` を編集した後に実行する。

```bash
python3 ../skill-creator/scripts/quick_validate.py .
```

生成した plugin を渡す前に実行する。

```bash
python3 scripts/validate_plugin.py <plugin-path>
```
