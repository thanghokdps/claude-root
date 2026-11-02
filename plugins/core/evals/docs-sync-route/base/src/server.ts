import express from "express";
import { orders } from "./routes/orders";

const app = express();
app.use(express.json());
app.use("/", orders);
app.listen(3000);
