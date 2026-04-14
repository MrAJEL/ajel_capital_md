FROM node:18-alpine

WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm install

# Copy all files
COPY . .

# Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED 1

# Start the dev server
CMD ["npm", "run", "dev"]
