IMAGE:=uhub.service.ucloud.cn/wumitech.com/jarvis
TAG:=2512201001

.PHONY: build
build:
	docker buildx build -t ${IMAGE}:${TAG} . --platform=linux/amd64

.PHONY: build-mac
build-mac:
	docker buildx build -t ${IMAGE}:${TAG} . --platform=darwin/arm64

.PHONY: push
push:
	docker push ${IMAGE}:${TAG}

.PHONY: deploy
deploy:
	docker-compose up -d