package openapiart_test

import (
	"context"
	"fmt"
	"log"
	"net"

	"github.com/golang/protobuf/ptypes/empty"
	sanity "github.com/open-traffic-generator/openapiart/pkg/sanity"

	"google.golang.org/grpc"
)

var (
	testPort   uint         = 40051
	testServer *grpc.Server = nil
	config     *sanity.PrefixConfig
)

type server struct {
	sanity.UnimplementedOpenapiServer
}

func StartMockServer() error {
	if testServer != nil {
		log.Print("MockServer: Server already running")
		return nil
	}

	addr := fmt.Sprintf("[::]:%d", testPort)
	lis, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatal(fmt.Sprintf("MockServer: Server failed to listen on address %s", addr))
	}

	svr := grpc.NewServer()
	log.Print(fmt.Sprintf("MockServer: Server started and listening on address %s", addr))

	sanity.RegisterOpenapiServer(svr, &server{})
	log.Print("MockServer: Server subscribed with gRPC Protocol Service")

	go func() {
		if err := svr.Serve(lis); err != nil {
			log.Fatal("MockServer: Server failed to serve for incoming gRPC request.")
		}
	}()

	testServer = svr
	return nil
}

func (s *server) SetConfig(ctx context.Context, req *sanity.SetConfigRequest) (*sanity.SetConfigResponse, error) {
	var resp *sanity.SetConfigResponse
	switch req.PrefixConfig.Response.Enum().Number() {
	case sanity.PrefixConfig_Response_status_400.Enum().Number():
		resp = &sanity.SetConfigResponse{
			StatusCode_400: &sanity.SetConfigResponse_StatusCode400{
				ErrorDetails: &sanity.ErrorDetails{
					Errors: []string{"SetConfig has detected configuration errors"},
				},
			},
		}
	case sanity.PrefixConfig_Response_status_500.Enum().Number():
		resp = &sanity.SetConfigResponse{
			StatusCode_500: &sanity.SetConfigResponse_StatusCode500{
				Error: &sanity.Error{
					Errors: []string{"SetConfig has encountered a server error"},
				},
			},
		}
	case sanity.PrefixConfig_Response_status_200.Enum().Number():
		config = req.PrefixConfig
		resp = &sanity.SetConfigResponse{
			StatusCode_200: &sanity.SetConfigResponse_StatusCode200{
				Bytes: []byte("SetConfig has completed successfully"),
			},
		}
	}
	return resp, nil
}

func (s *server) GetConfig(ctx context.Context, req *empty.Empty) (*sanity.GetConfigResponse, error) {
	resp := &sanity.GetConfigResponse{
		StatusCode_200: &sanity.GetConfigResponse_StatusCode200{
			PrefixConfig: config,
		},
	}
	return resp, nil
}

func (s *server) UpdateConfig(ctx context.Context, req *sanity.UpdateConfigRequest) (*sanity.UpdateConfigResponse, error) {
	resp := &sanity.UpdateConfigResponse{
		StatusCode_200: &sanity.UpdateConfigResponse_StatusCode200{
			PrefixConfig: config,
		},
	}
	return resp, nil
}
