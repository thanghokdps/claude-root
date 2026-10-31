---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill, Edit, Write]
tags: [api-client]
---

Tích hợp API vận chuyển của bên shipping vào backend giúp tôi. Đây là spec của họ:

```yaml
openapi: 3.0.3
info: {title: Shipfast API, version: "1.0"}
servers: [{url: https://api.shipfast.example/v1}]
security: [{apiKey: []}]
paths:
  /shipments:
    post:
      summary: Create a shipment
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [order_ref, address]
              properties:
                order_ref: {type: string}
                address: {type: string}
      responses:
        "201": {description: created, content: {application/json: {schema: {$ref: "#/components/schemas/Shipment"}}}}
        "422": {description: invalid address}
    get:
      summary: List shipments (paginated)
      parameters:
        - {name: cursor, in: query, schema: {type: string}}
        - {name: limit, in: query, schema: {type: integer, maximum: 100}}
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  items: {type: array, items: {$ref: "#/components/schemas/Shipment"}}
                  next_cursor: {type: string, nullable: true}
  /shipments/{id}:
    get:
      summary: Get one shipment
      responses:
        "200": {description: ok, content: {application/json: {schema: {$ref: "#/components/schemas/Shipment"}}}}
        "404": {description: not found}
components:
  securitySchemes:
    apiKey: {type: apiKey, in: header, name: X-Api-Key}
  schemas:
    Shipment:
      type: object
      properties:
        id: {type: string}
        order_ref: {type: string}
        status: {type: string, enum: [pending, in_transit, delivered]}
```
