FROM golang:1.25.1-alpine AS builder

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY services/blockchain_service/go.mod services/blockchain_service/go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -o authchain ./services/blockchain_service/cmd/main.go

FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache ca-certificates
COPY --from=builder /app/authchain /app/authchain
RUN mkdir -p /app/data
ENV GIN_MODE=release
EXPOSE 8081
ENTRYPOINT ["/app/authchain"]