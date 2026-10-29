import { Router } from "express";
import { all, byId, refund } from "../services/orders";

export const orders = Router();

orders.get("/orders", function listOrders(_req, res) {
  res.json(all());
});

orders.get("/orders/:id", function getOrder(req, res) {
  const order = byId(req.params.id);
  order ? res.json(order) : res.sendStatus(404);
});

orders.post("/orders/:id/refund", function refundOrder(req, res) {
  const order = refund(req.params.id);
  order ? res.json(order) : res.sendStatus(409);
});
