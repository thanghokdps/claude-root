import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export async function greeting(id: number): Promise<string> {
  const user = await prisma.user.findUniqueOrThrow({ where: { id } });
  return `Hello, ${user.fullName}`;
}
