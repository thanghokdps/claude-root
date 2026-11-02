FROM node:latest
ENV PAYMENTS_API_KEY=FAKE-PAYMENTS-KEY-DO-NOT-USE-0000
WORKDIR /app
COPY . .
RUN npm install
EXPOSE 3000
CMD ["node", "src/server.js"]
