/**
 * Vercel serverless catch-all for the Express API server.
 *
 * Vercel compiles this file with @vercel/node and serves it at /api/*.
 * All requests that don't match a more specific function (e.g. /api/webhook.py)
 * are routed here and forwarded to the Express app unchanged.
 *
 * The Express app is imported — NOT started with app.listen() — so Vercel's
 * runtime owns the HTTP lifecycle.
 */
import app from "../artifacts/api-server/src/app";

export default app;
