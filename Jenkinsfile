pipeline {
    agent any

    environment {
        REPO_ADDRESS = 'localhost:5000'
        ARCH = sh(script: 'uname -m', returnStdout: true).trim()
        BRANCH = "${BRANCH_NAME}"
        IMAGE_NAME = "gps-mqtt-app"
        TAG = "${IMAGE_NAME}:${ARCH}-${BRANCH}"
        DOCKER_BUILDKIT = '1'
    }

    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    sh 'ls'
                    sh 'docker build -t ${TAG} .'
                    sh 'docker tag ${TAG} ${REPO_ADDRESS}/${TAG}'
                    if (BRANCH == 'master') {
                        sh 'docker tag ${TAG} ${REPO_ADDRESS}/${IMAGE_NAME}:${ARCH}-stable'
                        sh 'docker tag ${TAG} ${REPO_ADDRESS}/${IMAGE_NAME}:stable'
                    } else if (BRANCH == 'dev') {
                        sh 'docker tag ${TAG} ${REPO_ADDRESS}/${IMAGE_NAME}:${ARCH}-latest'
                        sh 'docker tag ${TAG} ${REPO_ADDRESS}/${IMAGE_NAME}:latest'
                    }
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    sh 'docker push ${REPO_ADDRESS}/${TAG}'
                    if (BRANCH == 'master') {
                        sh 'docker push ${REPO_ADDRESS}/${IMAGE_NAME}:${ARCH}-stable'
                        sh 'docker push ${REPO_ADDRESS}/${IMAGE_NAME}:stable'
                    } else if (BRANCH == 'dev') {
                        sh 'docker push ${REPO_ADDRESS}/${IMAGE_NAME}:${ARCH}-latest'
                        sh 'docker push ${REPO_ADDRESS}/${IMAGE_NAME}:latest'
                    }
                }
            }
        }
    }
}
