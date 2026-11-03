// Vercel Routing Middleware: Basic Auth in front of every page of the docs site. The password is the
// Vercel env var SITE_PASSWORD (any user name); unset, the site stays locked rather than open.
import { createHash, timingSafeEqual } from "node:crypto";

export const config = { runtime: "nodejs" };

const digest = (text) => createHash("sha256").update(text).digest();

export default function middleware(request) {
  const password = process.env.SITE_PASSWORD;
  if (!password)
    return new Response("Site locked: SITE_PASSWORD is not set.", {
      status: 503,
    });

  const [scheme, encoded] = (request.headers.get("authorization") || "").split(
    " ",
  );
  if (scheme === "Basic" && encoded) {
    const credentials = Buffer.from(encoded, "base64").toString("utf8");
    const colon = credentials.indexOf(":");
    // Returning nothing lets the request through to the static file.
    if (
      colon >= 0 &&
      timingSafeEqual(digest(credentials.slice(colon + 1)), digest(password))
    )
      return;
  }
  return new Response("Authentication required.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="docs", charset="UTF-8"' },
  });
}
