apt-get install -y libjpeg8-dev openssl ssl-cert
go get github.com/barnacs/compy
cd go/src/github.com/barnacs/compy/
go install

openssl req -x509 -newkey rsa:2048 -nodes -keyout cert.key -out cert.crt -days 3650 -subj '/CN=<your-domain>'

cd go/src/github.com/barnacs/compy/
compy -cert cert.crt -key cert.key -ca ca.crt -cakey ca.key

go install github.com/google/pprof@latest

apt-get install graphviz

cd go/src/github.com/barnacs/compy/
go test -bench=. -cpuprofile=cpu.prof
go tool pprof -http=:9980 cpu.prof