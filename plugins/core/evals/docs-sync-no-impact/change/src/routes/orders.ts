import { Router } from "express";
import { all, byId } from "../services/orders";

export const orders = Router();

orders.get("/orders", function listOrders(_req, res) {
  res.json(all());
});

orders.get("/orders/:id", function getOrder(req, res) {
  const found = byId(req.params.id);
  found ? res.json(found) : res.sendStatus(404);
});
