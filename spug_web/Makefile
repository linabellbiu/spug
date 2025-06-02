version=v$(shell date +"%Y.%m.%d-%H.%M.%S")
DOCKER_REPO=crpi-4x4qgscmgn5y910k.cn-shenzhen.personal.cr.aliyuncs.com/zrxyappserver/spug

build-spug:
	docker build --platform linux/amd64 --build-arg ENV=prod -t ${DOCKER_REPO} .
	docker tag ${DOCKER_REPO} ${DOCKER_REPO}:${version}-prod
	docker push ${DOCKER_REPO}:${version}-prod
