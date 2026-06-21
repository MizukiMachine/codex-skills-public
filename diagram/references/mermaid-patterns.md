# Mermaid図パターン / Mermaid Diagram Patterns

## 目次 / Table of Contents
1. [テーマ設定 / Theme Configuration](#theme-configuration)
2. [配色 / Color Schemes](#color-schemes)
3. [システムコンテキスト / C4 System Context](#c4-system-context)
4. [コンテナ / C4 Container](#c4-container)
5. [レイヤードアーキテクチャ / Layered Architecture](#layered-architecture)
6. [コンポーネント図 / Component Diagram](#component-diagram)
7. [データフロー / Data Flow](#data-flow)
8. [シーケンス図 / Sequence Diagram](#sequence-diagram)
9. [エンティティ関係図 / ER Diagram](#er-diagram)
10. [状態図 / State Diagram](#state-diagram)
11. [デプロイ図 / Deployment Diagram](#deployment-diagram)
12. [依存関係図 / Dependency Diagram](#dependency-diagram)

---

## テーマ設定 / Theme Configuration

カスタム色つきの基本テーマ / Base theme with custom colors:
```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'primaryColor': '#7FB3D0',
  'primaryTextColor': '#333',
  'primaryBorderColor': '#5DADE2',
  'lineColor': '#85929E'
}}}%%
```

---

## 配色 / Color Schemes

### レイヤー色 / Layer Colors - Pastel Palette
| レイヤー / Layer | Fill | Stroke |
|-------|------|--------|
| 入口 / Entry | `#5D6D7E` | `#4A4d60` |
| 表示 / Presentation | `#F5B7b1` | `#D98880` |
| アプリケーション / Application | `#FAD7A0` | `#C68A00` |
| サービス / Service | `#F9E79F` | `#D4AC00` |
| ドメイン / Domain | `#A9DFBF` | `#52BE80` |
| データアクセス / Data Access | `#A3E4D7` | `#48C9B0` |
| インフラ / Infrastructure | `#AED6F1` | `#5DADE2` |

### 地域色 / Region Colors - Pastel Palette
| 地域 / Region | Fill | Stroke |
|--------|------|--------|
| JP | `#FADBD8` | `#D98880` |
| US | `#FCF3CF` | `#F4D03F` |
| EU | `#D7BDE2` | `#BB8FCE` |

### コンポーネント色 / Component Colors - Pastel Palette
| 種別 / Type | Fill | Stroke |
|------|------|--------|
| コア / Core | `#AED6F1` | `#5DADE2` |
| データ / Data | `#A3E4D7` | `#48C9B0` |
| 入力 / Input | `#AED6F1` | `#5DADE2` |
| 処理 / Process | `#FAD7A0` | `#F5B041` |
| 出力 / Output | `#A9DFBF` | `#52BE80` |

---
## システムコンテキスト / C4 System Context
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph External["外部システム / External Systems"]
        MobileApp["[Mobile App] モバイルアプリ<br/>Mobile App"]
        AdminConsole["[Admin Console] 管理コンソール<br/>Admin Console"]
    end

    subgraph System["システム名 / System Name"]
        Core["[Core Service] コアサービス<br/>Core Service"]
    end
    MobileApp -->|"HTTPS<br/>リクエスト"| Core
    AdminConsole -->|"HTTPS<br/>管理操作"| Core

    style System fill:#E8F4FD,stroke:#2E5A8B,stroke-width:3px
    style External fill:#F4F6F7,stroke:#5D6D7E
```

---

## コンテナ / C4 Container
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph Cloud["クラウド基盤 / Cloud Platform"]
        subgraph Global["グローバル / Global"]
            LB["[Load Balancer] 負荷分散<br/>Load Balancer"]
        end
        subgraph Region["リージョン / Region"]
            API["[API Server] APIサーバ<br/>API Server"]
            DB[("データベース<br/>Database")]
        end
    end
    LB --> API
    API --> DB
    style Cloud fill:#E8F4FD,stroke:#2E5A8B
```

---
## レイヤードアーキテクチャ / Layered Architecture
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph L4["レイヤ4: プレゼンテーション / Presentation"]
        UI["UIコンポーネント<br/>UI Components"]
    end
    subgraph L3["レイヤ3: アプリケーション / Application"]
        Service["アプリケーションサービス<br/>Application Services"]
    end
    subgraph L2["レイヤ2: ドメイン / Domain"]
        Entity["ドメインエンティティ<br/>Domain Entities"]
    end
    subgraph L1["レイヤ1: インフラ / Infrastructure"]
        DB[("データベース<br/>Database")]
    end
    UI --> Service
    Service --> Entity
    Entity --> DB
    style L4 fill:#F5B7B1,stroke:#D98880,color:#333
    style L3 fill:#FAD7A0,stroke:#C68A00,color:#333
    style L2 fill:#A9DFBF,stroke:#52BE80,color:#333
    style L1 fill:#AED6F1,stroke:#5DADE2,color:#333
```

---
## コンポーネント図 / Component Diagram
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph Core["コアモジュール / Core Module"]
        Handler["ハンドラー<br/>Handler"]
        Service["サービス<br/>Service"]
    end
    subgraph Data["データ層 / Data Layer"]
        Repository["リポジトリ<br/>Repository"]
        ORM["O/Rマッパー<br/>ORM"]
    end
    Handler --> Service
    Service --> Repository
    Repository --> ORM
    style Core fill:#AED6F1,stroke:#5DADE2,color:#333
    style Data fill:#A3E4D7,stroke:#48C9B0,color:#333
```

---
## データフロー / Data Flow
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart LR
    subgraph Input["入力 / Input"]
        A[("受信<br/>Receive")]
    end
    subgraph Process["処理 / Process"]
        B["変換<br/>Transform"]
        C["検証<br/>Validate"]
    end
    subgraph Output["出力 / Output"]
        D[("保存<br/>Store")]
    end
    A -->|"生データ / Raw Data"| B
    B -->|"変換済み / Transformed"| C
    C -->|"有効 / Valid"| D
    style Input fill:#AED6F1,stroke:#5DADE2,color:#333
    style Process fill:#FAD7A0,stroke:#F5B041,color:#333
    style Output fill:#A9DFBF,stroke:#52BE80,color:#333
```

---
## シーケンス図 / Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    participant C as クライアント<br/>Client
    participant S as サーバー<br/>Server
    participant DB as データベース<br/>Database
    Note over C,DB: リクエスト処理フロー / Request Flow
    C->>S: リクエスト<br/>Request
    activate S
    S->>DB: クエリ<br/>Query
    activate DB
    DB-->>S: 結果<br/>Result
    deactivate DB
    S-->>C: レスポンス<br/>Response
    deactivate S
```

---
## エンティティ関係図 / ER Diagram
```mermaid
erDiagram
    %% エンティティ定義 / Entity Definitions
    User {
        string ID PK "ユーザーID / User ID"
        string Name "名前 / Name"
        timestamp CreatedAt "作成日時 / Created At"
    }
    Order {
        string ID PK "注文ID / Order ID"
        string UserID FK "ユーザーID / User ID"
        int64 Total "合計 / Total"
    }
    %% リレーション / Relations
    User ||--o{ Order : "発注 / places"
```

---
## 状態図 / State Diagram
```mermaid
stateDiagram-v2
    [*] --> Idle
    state Idle {
        [*] --> Waiting
    }
    Idle --> Processing : イベント受信 / Event Received
    state Processing {
        [*] --> Validating
        Validating --> Executing
        Executing --> [*]
    }
    Processing --> Idle : 完了 / Completed
    Idle --> [*] : 終了 / End
```

---
## デプロイ図 / Deployment Diagram
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph Internet["インターネット / Internet"]
        Client["クライアント<br/>Client"]
    end
    subgraph Cloud["クラウドプラットフォーム / Cloud Platform"]
        subgraph Compute["コンピュート / Compute"]
            Server["サーバーインスタンス<br/>Server Instance"]
        end
        subgraph Storage["ストレージ / Storage"]
            DB[("マネージドDB<br/>Managed DB")]
        end
    end
    Client -->|"HTTPS"| Server
    Server --> DB
    style Cloud fill:#E8F4FD,stroke:#2E5A8B
    style Internet fill:#F4F6F7,stroke:#5D6D7E
```

---
## 依存関係図 / Dependency Diagram
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart BT
    subgraph Layer1["レイヤ1: 基盤 / Foundation"]
        Core["コアモジュール<br/>Core Module"]
    end
    subgraph Layer2["レイヤ2: サービス / Services"]
        SvcA["サービスA<br/>Service A"]
        SvcB["サービスB<br/>Service B"]
    end
    subgraph Layer3["レイヤ3: アプリケーション / Application"]
        App["アプリケーション<br/>Application"]
    end
    SvcA --> Core
    SvcB --> Core
    App --> SvcA
    App --> SvcB
    style Layer1 fill:#AED6F1,stroke:#5DADE2,color:#333
    style Layer2 fill:#A3E4D7,stroke:#48C9B0,color:#333
    style Layer3 fill:#F5B7B1,stroke:#D98880,color:#333
```
