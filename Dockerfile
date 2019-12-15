FROM alexellis2/go-armhf:1.9

RUN apk add --update git &&\
	rm -rf /var/cache/apk/* 

WORKDIR /go/src/github.com/bestander/mars-rover

COPY main.go .
RUN go get
RUN go install

CMD ["mars-rover"]

