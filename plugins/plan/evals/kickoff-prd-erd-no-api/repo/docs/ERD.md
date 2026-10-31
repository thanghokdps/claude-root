# ERD

```mermaid
erDiagram
    MEMBER ||--o{ BOOKING : makes
    CLASS ||--o{ BOOKING : has
    MEMBER ||--o{ CREDIT_PACK : buys
    MEMBER { uuid id string email }
    CLASS { uuid id datetime starts_at int seats }
    BOOKING { uuid id uuid member_id uuid class_id string status }
    CREDIT_PACK { uuid id uuid member_id int credits_left }
```
