const fs = require('fs');

var dockerHubAPI = require('docker-hub-api');
dockerHubAPI.login(process.env.DOCKER_USER,
                   process.env.DOCKER_PASS)
    .then((x) => dockerHubAPI.setLoginToken(x.token))
    .then(() => {
        const readme = fs.readFileSync(process.argv[4] || '/tmp/README.md',
                                       {encoding: 'utf-8'});
        dockerHubAPI.setRepositoryDescription(process.argv[2],
                                              process.argv[3],
                                              {full: readme});
    });
