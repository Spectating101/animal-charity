FROM node:20-alpine
WORKDIR /app
COPY package.json ./
COPY src ./src
COPY public ./public
COPY data ./data
ENV PORT=3000
EXPOSE 3000
CMD ["npm", "start"]
