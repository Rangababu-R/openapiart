package test

import (
	"bytes"
	"io/ioutil"

	"net/http"
	"net/http/httptest"
	"testing"

	"localdev/art_go/models"

	"github.com/stretchr/testify/assert"
)

func TestGetRootResponse(t *testing.T) {
	router := setup()
	req, _ := http.NewRequest(http.MethodGet, "/apitest", nil)
	wr := httptest.NewRecorder()
	router.ServeHTTP(wr, req)
	assert.Equal(t, http.StatusOK, wr.Code)

	jsonResponse, _ := ioutil.ReadAll(wr.Body)
	r := models.NewCommonResponseSuccess()
	r.FromJson(string(jsonResponse))
	assert.Equal(t, "from GetRootResponse", r.Message())
}

func TestPostRootResponse(t *testing.T) {
	router := setup()
	req, _ := http.NewRequest(http.MethodPost, "/apitest", nil)
	wr := httptest.NewRecorder()
	router.ServeHTTP(wr, req)
	assert.Equal(t, http.StatusInternalServerError, wr.Code)

	inputbody := models.NewApiTestInputBody().SetSomeString("this is the input body")
	inputbuffer := bytes.NewBuffer([]byte(inputbody.ToJson()))

	req, _ = http.NewRequest(http.MethodPost, "/apitest", inputbuffer)
	wr = httptest.NewRecorder()
	router.ServeHTTP(wr, req)
	assert.Equal(t, http.StatusOK, wr.Code)

	jsonResponse, _ := ioutil.ReadAll(wr.Body)
	r := models.NewCommonResponseSuccess()
	r.FromJson(string(jsonResponse))
	assert.Equal(t, "this is the input body", r.Message())
}
