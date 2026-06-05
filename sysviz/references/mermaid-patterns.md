# Mermaid Diagram Patterns

## Table of Contents
1. [Theme Configuration](#theme-configuration)
2. [Color Schemes](#color-schemes)
3. [C4 System Context](#c4-system-context)
4. [C4 Container](#c4-container)
5. [Layered Architecture](#layered-architecture)
6. [Component Diagram](#component-diagram)
7. [Data Flow](#data-flow)
8. [Sequence Diagram](#sequence-diagram)
9. [ER Diagram](#er-diagram)
10. [State Diagram](#state-diagram)
11. [Deployment Diagram](#deployment-diagram)
12. [Dependency Diagram](#dependency-diagram)

---

## Theme Configuration

Base theme with custom colors:
```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'primaryColor': '#7FB3D0',
  'primaryTextColor': '#333',
  'primaryBorderColor': '#5DADE2',
  'lineColor': '#85929E'
}}}%%
```

---

## Color Schemes

### Layer Colors (top to bottom) - Pastel Palette
| Layer | Fill | Stroke |
|-------|------|--------|
| Entry | `#5D6D7E` | `#4A4d60` |
| Presentation | `#F5B7b1` | `#D98880` |
| Application | `#FAD7A0` | `#C68A00` |
| Service | `#F9E79F` | `#D4AC00` |
| Domain | `#A9DFBF` | `#52BE80` |
| Data Access | `#A3E4D7` | `#48C9B0` |
| Infrastructure | `#AED6F1` | `#5DADE2` |

### Region Colors - Pastel Palette
| Region | Fill | Stroke |
|--------|------|--------|
| JP | `#FADBD8` | `#D98880` |
| US | `#FCF3CF` | `#F4D03F` |
| EU | `#D7BDE2` | `#BB8FCE` |

### Component Colors - Pastel Palette
| Type | Fill | Stroke |
|------|------|--------|
| Core | `#AED6F1` | `#5DADE2` |
| Data | `#A3E4D7` | `#48C9B0` |
| Input | `#AED6F1` | `#5DADE2` |
| Process | `#FAD7A0` | `#F5B041` |
| Output | `#A9DFBF` | `#52BE80` |

---
## C4 System Context
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph External["外部システム / External Systems"]
        MobileApp["[Mobile App]<br/>モバイルアプリ"]
        AdminConsole["[Admin Console]<br/>管理コンソール"]
    end

    subgraph System["システム名 / System Name"]
        Core["[Core Service]<br/>コアサービス"]
    end
    MobileApp -->|"HTTPS<br/>リクエスト"| Core
    AdminConsole -->|"HTTPS<br/>管理操作"| Core

    style System fill:#E8F4FD,stroke:#2E5A8B,stroke-width:3px
    style External fill:#F4F6F7,stroke:#5D6D7E
```

---

## C4 Container
```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#7FB3D0'}}}%%
flowchart TB
    subgraph Cloud["Cloud Platform"]
        subgraph Global["グローバル / Global"]
            LB["[Load Balancer]<br/>負荷分散"]
        end
        subgraph Region["リージョン / Region"]
            API["[API Server]<br/>アプリケーション"]
            DB[("Database<br/>データベース")]
        end
    end
    LB --> API
    API --> DB
    style Cloud fill:#E8F4FD,stroke:#2E5A8B
```

---
## Layered Architecture
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
## Component Diagram
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
## Data Flow
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
## Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    participant C as Client<br/>クライアント
    participant S as Server<br/>サーバー
    participant DB as Database<br/>データベース
    Note over C,DB: リクエスト処理フロー / Request Flow
    C->>S: Request<br/>リクエスト
    activate S
    S->>DB: Query<br/>クエリ
    activate DB
    DB-->>S: Result<br/>結果
    deactivate DB
    S-->>C: Response<br/>レスポンス
    deactivate S
```

---
## ER Diagram
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
## State Diagram
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
## Deployment Diagram
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
## Dependency Diagram
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
