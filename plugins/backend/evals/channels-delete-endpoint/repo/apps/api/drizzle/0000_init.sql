CREATE TABLE "workspaces" (
	"id" serial PRIMARY KEY NOT NULL,
	"name" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "users" (
	"id" serial PRIMARY KEY NOT NULL,
	"workspace_id" integer NOT NULL REFERENCES "workspaces"("id") ON DELETE CASCADE,
	"email" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "channels" (
	"id" serial PRIMARY KEY NOT NULL,
	"workspace_id" integer NOT NULL REFERENCES "workspaces"("id") ON DELETE CASCADE,
	"created_by" integer NOT NULL REFERENCES "users"("id") ON DELETE RESTRICT,
	"name" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE INDEX "channels_workspace_id_idx" ON "channels" ("workspace_id");
--> statement-breakpoint
CREATE UNIQUE INDEX "channels_workspace_name_idx" ON "channels" ("workspace_id", "name");
