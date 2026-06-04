---
name: site-metadata-generator
description: "WebプロジェクトのSEO・SNS向けメタデータを生成・監査・実装する。Open Graph、Twitterカード、canonical、robots、sitemap、構造化データで使う。"
---

# Site Metadata Generator

## 目的

Web project を search engine、social platform、AI crawler が理解できる状態にする。汎用的な SEO 文章ではなく、framework-native metadata、structured data、crawlability files、簡潔な audit trail を作る。

## 基本方針

metadata は semantic communication として扱う。正しい output は、ページが実際に何で、誰のためのもので、機械がどう分類すべきかを説明する。

優先順位:

1. 正確な page meaning と user intent
2. crawlability、canonical URLs、robots.txt、sitemap coverage
3. framework-native metadata APIs と既存 project conventions
4. 重要ページごとの unique titles、descriptions、social tags
5. ページに実在する内容だけを表す JSON-LD
6. discoverability に影響する performance と mobile issues

実装前に確認すること:

- framework、router、build tool、既存 metadata conventions
- site name、canonical domain、locale、default social image、brand voice
- page types: home、product、service、article、documentation、FAQ、contact、legal、app-only
- 依頼が audit、implementation、sitemap generation、structured-data work、または全部か
- credentials や production access なしで実行できる check は何か

## 契約

- production domain、ratings、prices、review counts、author names、publish dates、addresses、phone numbers、social handles を捏造しない。必要な事実が見つからない場合は質問するか、明確な project-local placeholder を残す
- canonical URLs、`og:url`、sitemap URLs、robots sitemap links は同じ production origin と trailing-slash policy を使う
- sitemaps には indexing 対象の canonical URLs だけを入れる。admin、API、auth、search result、redirect、draft、duplicate、`noindex` pages は除外する
- JSON-LD は valid JSON にし、framework が正しく render する方法で inject し、visible または verifiable content に限定する
- metadata ownership は1箇所に寄せる。layout、route、component、CMS layers に title/canonical/Open Graph/JSON-LD が競合しないようにする
- social image URL は production で resolve できるようにする。framework が configured metadata base から確実に相対 asset を展開しない限り、absolute URL を使う

canonical production domain、target locale、必須の business facts が見つからず、generated URLs や structured data に大きく影響する場合だけ、編集前に短く質問する。それ以外は保守的に実装し、仮定を記録する。

## Capabilities and Deliverables

このスキルで扱うこと:

- current metadata、crawlability、sitemap、robots、social tags、JSON-LD coverage の audit
- project native framework pattern による missing metadata の実装
- `robots.txt`、framework robots routes、`sitemap.xml`、framework sitemap routes の生成または更新
- content を捏造しない page-appropriate Schema.org JSON-LD の追加
- blocking issues、quick wins、changed files、verification results を含む focused findings summary

成果物の例:

- route、layout、SEO helper、content/frontmatter、config、public asset、robots、sitemap files の編集
- metadata pattern が page type ごとにわかる map
- review 依頼の場合の短い audit report
- local validation output と、deployed URLs や external accounts が必要で未実行の checks の明記

## 参照ファイル

必要な reference だけを読む。

| Topic | File | Use When |
|-------|------|----------|
| Audit checklist | [analysis-checklist.md](references/analysis-checklist.md) | 現在の SEO、crawlability、social tags、schema、performance、mobile basics を review するとき |
| Framework patterns | [framework-implementations.md](references/framework-implementations.md) | Next.js、Astro、Gatsby、React、Vue/Nuxt、static HTML で metadata を実装するとき |
| Complete tag reference | [meta-tags-complete.md](references/meta-tags-complete.md) | meta、Open Graph、Twitter、canonical、robots、verification tags を正確に選ぶとき |
| Structured data | [structured-data-schemas.md](references/structured-data-schemas.md) | Organization、WebSite、Article、Product、FAQPage、BreadcrumbList、LocalBusiness、Event、HowTo JSON-LD を追加するとき |

## ワークフロー

1. project shape を調べる。

   ```bash
   rg --files | rg '(^|/)(package\.json|next\.config\.(js|mjs|ts)|astro\.config\.(mjs|ts)|gatsby-config\.(js|ts)|nuxt\.config\.(js|ts)|vite\.config\.(js|ts)|index\.html|robots\.txt|sitemap\.xml|src/|app/|pages/|public/|static/)'
   rg -n "metadata|generateMetadata|<Head|next/head|react-helmet|Helmet|useHead|<title>|meta name=|property=\"og:|twitter:|application/ld\\+json|canonical|robots" .
   ```

   output が多い場合は target route や page folder に絞る。

2. 有用な場合は同梱 analyzer を実行する。

   ```bash
   python3 <skill-dir>/scripts/analyze_seo.py <project-path>
   ```

   `<skill-dir>` はこの `SKILL.md` がある directory に置き換える。出力は出発点であり、完全な判断ではない。common files と tags は検出するが、dynamic metadata や content strategy をすべて理解できるわけではない。

3. page types と metadata ownership を特定する。

   metadata が root layout、route-level file、page component、content collection、CMS data、shared helper のどこに属するか決める。新しい abstraction を足す前に既存 helper と naming conventions を使う。

4. site の metadata contract を定義する。

   canonical origin、trailing slash policy、default locale、site name、default social image、noindex rules、page facts の source を決める。必要な情報が不明なら production URL を書く前に確認する。

5. page truth から metadata を書く。

   title は unique で通常 50-60 characters、description は unique かつ正確で通常 150-160 characters。social metadata はやや click-oriented でもよいが、content と一致させる。

6. visible content に裏付けられる場合だけ structured data を追加する。

   JSON-LD と `@context: "https://schema.org"` を優先する。複数 schema が必要な場合は `@graph` を使う。Product、Review、FAQ、Event、LocalBusiness の property はページに実際に出ていないものを追加しない。

7. crawlability files がなければ追加する。

   `robots.txt`、framework-native robots routes、static `sitemap.xml`、framework-native sitemap routes を作るか更新する。sitemap には indexable canonical URLs だけを入れる。

8. local で検証する。

   利用できる最小の project checks を実行し、可能なら rendered HTML を確認し、生成した XML/JSON を validate する。external validators はユーザーが求めた場合、または local environment に access がある場合だけ使う。

## 実装ガイド

### Metadata Essentials

indexable page には次が必要。

```html
<title>Page Title | Site Name</title>
<meta name="description" content="Accurate page-specific summary.">
<link rel="canonical" href="https://example.com/page">
<meta property="og:type" content="website">
<meta property="og:url" content="https://example.com/page">
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Accurate page-specific summary.">
<meta property="og:image" content="https://example.com/og-image.png">
<meta name="twitter:card" content="summary_large_image">
```

framework が metadata API を持つ場合は、手書き tag ではなくそちらへ適用する。

### Page Type Decisions

| Page Type | Metadata Priority | Structured Data |
|-----------|-------------------|-----------------|
| Home or landing | Brand、category、primary value、default social image | Organization、WebSite、BreadcrumbList if relevant |
| Product or commerce | Product name、category、price/availability if present | Product、Offer、AggregateRating only when visible and true |
| Article or blog | Article title、author、publish/update dates、image | Article or BlogPosting、BreadcrumbList |
| Documentation | Precise task or concept、version if relevant | TechArticle、HowTo、FAQPage only for actual Q/A or steps |
| FAQ | Question-oriented title and summary | FAQPage |
| Local business | Service、city/region、contact intent | LocalBusiness with real address/hours/contact |
| Legal or account-only | Basic metadata、often noindex | Usually none |

### Sitemaps

static project 用、または route discovery aid として generator を使える。

```bash
python3 <skill-dir>/scripts/generate_sitemap.py <project-path> --domain https://example.com --output <project-path>/public/sitemap.xml
```

`<skill-dir>` はこの `SKILL.md` がある directory に置き換える。Next.js App Router、Astro integrations、Gatsby plugins、Nuxt modules などを既に使っている場合は framework-native sitemap route を優先する。admin、API、auth、search-result、duplicate、noindex、redirect、unpublished pages は除外する。

### Robots.txt

public site では permissive default から始め、private または non-indexable area だけ block する。

```txt
User-agent: *
Allow: /

Disallow: /admin/
Disallow: /api/
Disallow: /private/

Sitemap: https://example.com/sitemap.xml
```

staging / preview deployments は慎重に確認する。production の `Disallow: /` は blocking issue。unblocked staging site も blocking issue になり得る。

## Audit Mode

review または audit を求められた場合、実装メモではなく findings を先に出す。severity 順に並べる。

1. Blocking: deindexing risks、broken canonical host、invalid JSON-LD、noncanonical URLs だらけの sitemap、critical pages の metadata missing
2. Major: duplicated titles/descriptions、shareable pages の social metadata 欠落、key page types の structured data 欠落、crawl/render に影響する mobile/performance issues
3. Minor: wording refinements、optional verification tags、lower-priority schema opportunities、metadata consistency cleanup

各 finding には affected file or route、なぜ重要か、concrete fix を含める。観測された issue に結びつかない一般 SEO advice は入れない。

## 避けること

**Keyword stuffing**

問題: repetition は spammy snippets になり、page value を誤って伝える。

改善: 実際の page と search intent に合う specific title / description を書く。

**全ページ同一 description**

問題: search engines が duplicated descriptions を無視し、ユーザーがページを区別できない。

改善: 重要 route には page-specific descriptions を作り、low-priority pages だけ sensible default を使う。

**visible content のない schema**

問題: page に表示されない reviews、FAQs、prices、events、locations を structured data で主張すると search guidelines に反する可能性がある。

改善: ユーザーが見られる、または合理的に検証できる情報だけ schema にする。

**framework bypass**

問題: manual `<head>` tags は deduplicate、override、server rendering 漏れの原因になる。

改善: project の metadata API、layout convention、head component、plugin system を使う。

**route dump としての sitemap**

問題: noncanonical、private、duplicate、noindex URLs が crawl budget を浪費し、矛盾した signal を送る。

改善: indexing したい canonical URLs だけを含める。

## Variation Guidance

次に応じて変える。

- Framework: Next.js metadata API、Astro layout props、Gatsby Head exports、React Helmet、Vue/Nuxt head helpers、static HTML
- Industry: ecommerce、SaaS、local services、documentation、editorial、portfolio、event、app shell
- Locale and domain: canonical host、hreflang、region、translated metadata
- Page importance: key pages には comprehensive metadata、low-value pages には lightweight defaults
- Content source: hardcoded pages、markdown/frontmatter、CMS records、database routes、generated docs

避ける収束:

- every page type に同じ title format
- "Welcome to our website" のような generic descriptions
- dimensions 欠落または production で relative-only の social images
- site と一致しない example JSON-LD のコピー
- small native change で足りるのに broad SEO dependencies を追加する

## 検証

project に合う check を使う。

```bash
python3 <skill-dir>/scripts/analyze_seo.py .
python3 -m py_compile <skill-dir>/scripts/*.py
```

追加確認:

- 利用可能な project lint、typecheck、tests、build が通る
- rendered HTML に title が1つ、canonical URL が1つ、期待する description、social tags、有効な JSON-LD がある
- `robots.txt` と `sitemap.xml` が app の public output または framework route で reachable
- sitemap XML が parse でき、canonical URLs だけを含む
- JSON-LD が parse でき、trailing comments や framework escaping issues がない
- Open Graph image URL が production context で absolute で、実 image に resolve する

production credentials、deployed URLs、Search Console、external validators が必要で実行できなかった check は報告する。
