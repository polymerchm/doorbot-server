node {
    def app
    def branch_tag

    stage('Fetch') {
        checkout scm
    }

    stage('Build') {
        slackSend(
            color: 'good',
            message: "Started build of doorbot server [${env.BUILD_NUMBER} for ${env.BRANCH_NAME}] (<${env.BUILD_URL}|Open>)"
        )

        try {
        }
        catch( err ) {
            slackSend(
                color: '#ff0000',
                message: "Build ${env.BUILD_NUMBER} of doorbot server failed"
            )
            throw err
        }
    }
}
