import logging
import logging.handlers
import os
import glob
from datetime import datetime


class DailyRotatingWithSizeHandler(logging.handlers.TimedRotatingFileHandler):
    """
    일단위 로테이션 + 크기 초과시 추가 로테이션 핸들러
    
    특징:
    - 자정마다 자동 백업 (날짜_1.log)
    - 지정된 크기 초과시 즉시 백업 (날짜_2.log, 날짜_3.log...)
    - 파일명 형태: app_YYYYMMDD_N.log
    """
    
    def __init__(self, filename, maxBytes=20*1024*1024, **kwargs):
        """
        Args:
            filename: 기본 로그 파일명
            maxBytes: 최대 파일 크기 (기본: 20MB)
            **kwargs: TimedRotatingFileHandler의 기타 파라미터
        """
        # when="midnight"로 고정하고 다른 설정들 받음
        kwargs.setdefault('when', 'midnight')
        kwargs.setdefault('interval', 1)
        kwargs.setdefault('backupCount', 30)
        kwargs.setdefault('encoding', 'utf-8')
        
        super().__init__(filename, **kwargs)
        self.maxBytes = maxBytes
        self.base_filename = filename
        
    def _get_current_date_string(self):
        """현재 날짜 문자열 반환 (YYYYMMDD)"""
        return datetime.now().strftime("%Y%m%d")
    
    def _get_next_sequence_number(self, date_str):
        """해당 날짜의 다음 시퀀스 번호 계산"""
        log_dir = os.path.dirname(self.base_filename)
        base_name = os.path.splitext(os.path.basename(self.base_filename))[0]
        
        # 해당 날짜의 기존 파일들 찾기
        pattern = os.path.join(log_dir, f"{base_name}_{date_str}_*.log")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            return 1
        
        # 시퀀스 번호 추출하여 최대값 찾기
        max_seq = 0
        for file_path in existing_files:
            try:
                # app_20250627_3.log에서 3 추출
                seq_part = os.path.basename(file_path).split('_')[-1].split('.')[0]
                seq_num = int(seq_part)
                max_seq = max(max_seq, seq_num)
            except (ValueError, IndexError):
                continue
        
        return max_seq + 1
    
    def shouldRollover(self, record):
        """시간 또는 크기 조건 체크"""
        # 시간 기반 롤오버 체크 (자정)
        time_rollover = super().shouldRollover(record)
        
        # 크기 기반 롤오버 체크
        size_rollover = False
        if self.maxBytes > 0 and self.stream:
            msg = "%s\n" % self.format(record)
            current_size = self.stream.tell() + len(msg.encode('utf-8'))
            size_rollover = current_size >= self.maxBytes
        
        return time_rollover or size_rollover
    
    def doRollover(self):
        """롤오버 실행"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        current_date = self._get_current_date_string()
        
        # 현재 파일이 존재하면 백업
        if os.path.exists(self.baseFilename):
            # 시퀀스 번호 계산
            seq_num = self._get_next_sequence_number(current_date)
            
            # 백업 파일명 생성
            log_dir = os.path.dirname(self.base_filename)
            base_name = os.path.splitext(os.path.basename(self.base_filename))[0]
            backup_name = os.path.join(log_dir, f"{base_name}_{current_date}_{seq_num}.log")
            
            # 파일 이동
            try:
                os.rename(self.baseFilename, backup_name)
                print(f"로그 백업 생성: {backup_name}")
            except OSError as e:
                print(f"로그 백업 실패: {e}")
        
        # 오래된 백업 파일 정리 (backupCount 기준)
        self._cleanup_old_backups()
        
        # 새 파일 스트림 열기
        if not self.delay:
            self.stream = self._open()
    
    def _cleanup_old_backups(self):
        """오래된 백업 파일 정리"""
        if self.backupCount <= 0:
            return
        
        log_dir = os.path.dirname(self.base_filename)
        base_name = os.path.splitext(os.path.basename(self.base_filename))[0]
        
        # 모든 백업 파일 찾기
        pattern = os.path.join(log_dir, f"{base_name}_????????_*.log")
        backup_files = glob.glob(pattern)
        
        if len(backup_files) <= self.backupCount:
            return
        
        # 파일명으로 정렬 (날짜_시퀀스 순)
        backup_files.sort()
        
        # 오래된 파일들 삭제
        files_to_delete = backup_files[:-self.backupCount]
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f"오래된 로그 파일 삭제: {file_path}")
            except OSError as e:
                print(f"로그 파일 삭제 실패: {e}")


def create_daily_rotating_handler(
    log_dir: str,
    filename: str = "app.log",
    max_size_mb: int = 20,
    backup_count: int = 30
) -> DailyRotatingWithSizeHandler:
    """
    DailyRotatingWithSizeHandler 생성 팩토리 함수
    
    Args:
        log_dir: 로그 디렉토리 경로
        filename: 로그 파일명 (기본: app.log)
        max_size_mb: 최대 파일 크기 (MB 단위, 기본: 20MB)
        backup_count: 보관할 백업 파일 수 (기본: 30개)
    
    Returns:
        DailyRotatingWithSizeHandler 인스턴스
    """
    # 로그 디렉토리 생성
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 핸들러 생성
    handler = DailyRotatingWithSizeHandler(
        filename=os.path.join(log_dir, filename),
        maxBytes=max_size_mb * 1024 * 1024,  # MB를 바이트로 변환
        when="midnight",
        interval=1,
        backupCount=backup_count,
        encoding="utf-8"
    )
    
    return handler