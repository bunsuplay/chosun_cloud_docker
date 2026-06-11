# Presentation Tier 컨테이너 이미지
FROM nginx:alpine

# 기본 설정을 우리 설정으로 교체
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 프론트엔드 화면 파일 복사
COPY html/ /usr/share/nginx/html/

EXPOSE 80
